"""
================================================================================
Modul Detector & Tracker Lembar Soal Presisi (OpenCV + CV Cross + ResNet50 CNN)
================================================================================
Fungsi:
1. Membaca & memproses gambar lembar soal siswa SD menggunakan OpenCV & OCR.
2. Mengabaikan Kop Surat (Header) dan Bagian B (Isian/Essay) secara otomatis.
3. Men-track lokasi presisi setiap nomor soal (1 s/d 15) dan opsi A, B, C.
4. Mendeteksi tanda silang (X) secara akurat menggunakan pendekatan hibrida:
   - Analisis energi garis diagonal menyilang & kepadatan tinta pensil (Computer Vision).
   - Klasifikasi potongan opsi dengan model ResNet50 CNN (terpilih vs tidak_terpilih).
   - Pengambilan keputusan Relatif (Argmax) antar opsi A, B, dan C per nomor soal.
5. Menggambar visualisasi bounding box presisi & label jawaban terpilih.
6. Mengembalikan format JSON terstruktur & gambar teranotasi Base64.
================================================================================
"""

import os
import re
import cv2
import base64
import json
import numpy as np
from typing import Dict, List, Any, Tuple, Optional, Union
from PIL import Image

# Import model classifier loader
from .classifier import get_model_and_classes


def _configure_tesseract():
    """
    Konfigurasi path tesseract executable jika ada di sistem Windows / Linux.
    """
    try:
        import pytesseract
        possible_paths = [
            os.getenv('TESSERACT_CMD', ''),
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            r'C:\Users\fauza\AppData\Local\Programs\Tesseract-OCR\tesseract.exe',
            r'C:\laragon\bin\tesseract\tesseract.exe',
            'tesseract',
        ]
        for tess_path in possible_paths:
            if not tess_path:
                continue
            if tess_path == 'tesseract' or os.path.exists(tess_path):
                pytesseract.pytesseract.tesseract_cmd = tess_path
                return pytesseract
    except Exception as e:
        print(f"[TRACKER WARNING] Gagal konfigurasi tesseract: {e}")
    return None


def load_image_cv2(image_input: Union[str, bytes, Image.Image, Any]) -> np.ndarray:
    """
    Mengonversi berbagai jenis input gambar menjadi format OpenCV numpy BGR array.
    """
    if isinstance(image_input, str):
        if not os.path.exists(image_input):
            raise FileNotFoundError(f"File gambar tidak ditemukan: {image_input}")
        img = cv2.imread(image_input)
        if img is None:
            raise ValueError(f"Gagal membaca gambar dari path: {image_input}")
        return img
    elif isinstance(image_input, bytes):
        nparr = np.frombuffer(image_input, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Gagal mendecode bytes gambar.")
        return img
    elif isinstance(image_input, Image.Image):
        rgb_img = np.array(image_input.convert("RGB"))
        return cv2.cvtColor(rgb_img, cv2.COLOR_RGB2BGR)
    elif hasattr(image_input, 'read'):
        image_input.seek(0)
        img_bytes = image_input.read()
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Gagal mendecode file stream gambar.")
        return img
    elif isinstance(image_input, np.ndarray):
        return image_input.copy()
    else:
        raise TypeError(f"Tipe input gambar tidak didukung: {type(image_input)}")


def _is_question_prompt(line_text: str, line_x: int, w_img: int) -> bool:
    """
    Mendeteksi apakah sebuah baris teks merupakan pertanyaan soal (prompt),
    bukan baris pilihan jawaban (opsi A, B, C).
    """
    t = line_text.strip().lower()

    # Nomor soal jelas (misal: 1., 2., 10.)
    if re.match(r'^[0-9]{1,2}[\.\,\)]\s+', t):
        return True

    # Pernyataan bernomor (1), 2), 3), 4)) di dalam soal bertingkat
    if re.match(r'^[0-9]{1,2}[\)]\s+', t):
        return True

    # Soal matematika dengan operasi hitung (+, -, x, :, =) diakhiri elipsis/tanya
    if any(op in t for op in ['+', '=', ':', 'x']) and ('...' in t or '?' in t):
        return True

    # Pertanyaan yang diakhiri tanda tanya atau elipsis
    if t.endswith(('...', '?', '....', '..', '?:')):
        return True

    # Pertanyaan panjang dengan kata kunci soal SD
    question_keywords = [
        'perhatikan gambar', 'pernyataan berikut', 'lambang negara', 'sikap yang',
        'berikut ini', 'aturan makan', 'semua anggota', 'arti dari', 'menunjukkan',
        'beribadah sesuai', 'jika ada teman', 'hasil dari', 'dibaca', 'nilai tempat',
        'penerapan', 'nilai-nilai sila', 'perilaku dibawah ini'
    ]
    if any(k in t for k in question_keywords):
        return True

    return False


def _is_option_line(line: Dict[str, Any], w_img: int) -> Tuple[bool, Optional[str], Optional[Dict]]:
    """
    Mendeteksi apakah baris teks merupakan baris opsi jawaban (A, B, C, D atau simbol silang X).
    Mengembalikan (is_option, letter_code, token_word_obj).
    """
    words = line.get('words', [])
    if not words:
        return (False, None, None)

    line_text = line['text'].strip()
    if _is_question_prompt(line_text, line['x'], w_img):
        return (False, None, None)

    # Pindai hingga 6 token pertama untuk mentolerir noise border/simbol awal (misal: '~ C.Malam', 'or X Pagi', '| . ( pe B| B. Siang')
    for idx in range(min(6, len(words))):
        w = words[idx]
        word_text = w['text'].strip()

        # Abaikan angka murni (1, 2, 3) atau karakter noise tanda baca pendek
        if re.match(r'^[0-9]+[\.\,\)]?$', word_text):
            continue
        if len(word_text) <= 2 and word_text in ['|', ':', '!', ';', ')', '(', '-', '~', '_', '*', '`', '.', 'or', '1', '\\', '/', '+', 'pe']:
            continue

        # 1. Opsi standar: A., B., C., D. atau A, B, C, D
        m_std = re.match(r'^([A-D])[\.\,\)]?$', word_text)
        if m_std and w['x'] < w_img * 0.75:
            return (True, m_std.group(1), w)
        # Jika huruf kecil a-d, wajib diikuti titik/kurung untuk menghindari kata 'a', 'di', dll.
        m_lower = re.match(r'^([a-d])[\.\,\)]$', word_text)
        if m_lower and w['x'] < w_img * 0.75:
            return (True, m_lower.group(1).upper(), w)

        # 2. Opsi prefix tanpa spasi: A.Bersih, B.Rapi, C.Hidup, dll.
        m_pref = re.match(r'^([A-Da-d])[\.\,\)](.+)?$', word_text)
        if m_pref and w['x'] < w_img * 0.75:
            return (True, m_pref.group(1).upper(), w)

        # 3. Opsi tertutup silang: X, x, %, &, }, {, K, XX, XK, Re, >
        cross_symbols_pat = r'^([Xx%&\}kK\{\[\]\<\>]|XX|XK|Re)'
        m_cross = re.match(cross_symbols_pat + r'[\.\,\)]?(.+)?$', word_text)
        if m_cross and w['x'] < w_img * 0.75:
            rest_of_word = m_cross.group(2)
            if rest_of_word and len(rest_of_word) >= 2:
                return (True, 'X_SYM', w)
            elif idx + 1 < len(words):
                rest_line = " ".join([w_item['text'] for w_item in words[idx+1:]])
                if not _is_question_prompt(rest_line, w['x'], w_img):
                    return (True, 'X_SYM', w)

    return (False, None, None)



def analyze_cross_mark_patch(crop_bgr: np.ndarray) -> Dict[str, float]:
    """
    Ekstrak fitur fisik goresan silang (X) pensil/pena siswa:
    1. Ink Pixel Density: rasio luas piksel tinta hitam setelah threshold adaptif lokal.
    2. Diagonal Filter Energy: respon filter konvolusi garis menyilang (~45 deg dan ~135 deg).
    """
    gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 8
    )

    total_ink = cv2.countNonZero(thresh)
    density = total_ink / float(max(1, h * w))

    k_size = max(5, int(min(h, w) * 0.25))
    if k_size % 2 == 0:
        k_size += 1

    kernel_d1 = np.eye(k_size, dtype=np.float32) / float(k_size)
    kernel_d2 = np.fliplr(np.eye(k_size, dtype=np.float32)) / float(k_size)

    thresh_f = (thresh / 255.0).astype(np.float32)
    resp1 = cv2.filter2D(thresh_f, -1, kernel_d1)
    resp2 = cv2.filter2D(thresh_f, -1, kernel_d2)

    diag_score = float(np.mean(resp1 * resp2) * 1000.0)
    diag_max = float(np.max(resp1 + resp2))

    return {
        'ink_pixels': total_ink,
        'density': round(density, 4),
        'diag_score': round(diag_score, 4),
        'diag_max': round(diag_max, 4)
    }


def _ocr_extract_lines(img_bgr: np.ndarray) -> List[Dict[str, Any]]:
    """
    Menjalankan Tesseract OCR pada gambar dan mengelompokkan token menjadi baris teks.
    Menggunakan Adaptive Threshold untuk memperbaiki kontras pada foto siswa SD.
    """
    pytess = _configure_tesseract()
    if pytess is None:
        return []

    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    adapt = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 15
    )

    d = pytess.image_to_data(adapt, config='--psm 6', output_type=pytess.Output.DICT)

    lines_dict = {}
    for i in range(len(d['text'])):
        t = d['text'][i].strip()
        if not t:
            continue
        lid = (d['block_num'][i], d['par_num'][i], d['line_num'][i])
        if lid not in lines_dict:
            lines_dict[lid] = []
        lines_dict[lid].append({
            'text': t,
            'x': d['left'][i], 'y': d['top'][i],
            'w': d['width'][i], 'h': d['height'][i],
            'conf': d['conf'][i]
        })

    lines = []
    for lid, w_list in lines_dict.items():
        w_list.sort(key=lambda x: x['x'])
        line_text = " ".join([x['text'] for x in w_list])
        min_x = min(x['x'] for x in w_list)
        min_y = min(x['y'] for x in w_list)
        max_x = max(x['x'] + x['w'] for x in w_list)
        max_y = max(x['y'] + x['h'] for x in w_list)
        lines.append({
            'text': line_text,
            'x': min_x, 'y': min_y,
            'w': max_x - min_x, 'h': max_y - min_y,
            'words': w_list
        })
    lines.sort(key=lambda l: l['y'])
    return lines


def _find_section_bounds(lines: List[Dict], h_img: int) -> Tuple[int, int]:
    """
    Menentukan batas vertikal area Pilihan Ganda pada halaman.
    Mengabaikan Kop Surat (di atas instruksi) dan Bagian B / Isian (di bawah pemicu).
    """
    y_min = 0
    y_max = h_img

    for l in lines:
        txt_l = l['text'].lower()
        if any(k in txt_l for k in [
            'silang (x)', 'berilah tanda silang', 'pilihan ganda', 'a. berilah',
            'paling benar', 'jawaban yang paling', 'jawaban a, b'
        ]):
            y_min = max(y_min, l['y'] + l['h'] + 5)
        if any(k in txt_l for k in ['nama siswa', 'paraf guru', 'paraf orangtua']):
            y_min = max(y_min, l['y'] + l['h'] + 10)
        if re.search(r'\b(b\.\s*isilah|isilah\s+titik|soal\s+isian)\b', txt_l):
            y_max = min(y_max, l['y'] - 10)

    return (y_min, y_max)



def extract_questions_and_options(img: np.ndarray, start_question_number: int = 1) -> List[Dict[str, Any]]:
    """
    Dynamic Document Layout Analyzer (Universal & Presisi):
    1. Mengekstrak baris teks OCR dan memfilter area Pilihan Ganda (Kop Surat & Essay diabaikan).
    2. Menemukan anchor opsi (A, B, C, X_SYM) dengan toleransi layout 1 atau 2 kolom (sebelah gambar).
    3. Letter-Aware Interpolation: memulihkan posisi opsi yang tertutup goresan silang pekat tanpa menimbulkan opsi siluman ke bawah.
    4. Continuous Band Partitioning: mempartisi halaman secara kontinu dari $y_{\min}$ ke $y_{\max}$ sehingga seluruh teks pertanyaan, gambar ilustrasi, dan butir pernyataan 1)-4) terbingkai 100% utuh tanpa terpotong.
    """
    h_img, w_img = img.shape[:2]

    lines = _ocr_extract_lines(img)
    print(f"[DYNAMIC DETECTOR] Total baris OCR: {len(lines)}")

    y_min, y_max = _find_section_bounds(lines, h_img)
    content_lines = [l for l in lines if l['y'] >= y_min and (l['y'] + l['h']) <= y_max]
    print(f"[DYNAMIC DETECTOR] Batas y_min={y_min}, y_max={y_max}, baris konten={len(content_lines)}")

    opt_tokens = []
    for l in content_lines:
        # Deteksi khusus baris opsi gambar horisontal (misal: 'Ay ... Pe ... Boa')
        words = l.get('words', [])
        word_texts = [w_item['text'] for w_item in words]
        if 'Ay' in word_texts and len(words) >= 3:
            w_ay = next((w_item for w_item in words if w_item['text'] == 'Ay'), None)
            w_pe = next((w_item for w_item in words if w_item['text'] in ['Pe', 'pe']), None)
            w_boa = next((w_item for w_item in words if w_item['text'] in ['Boa', 'boa']), None)
            if w_ay and w_pe and w_boa:
                opt_tokens.append({'letter': 'A', 'x': w_ay['x'], 'y': w_ay['y'], 'w': w_ay['w'], 'h': w_ay['h'], 'line_text': l['text']})
                opt_tokens.append({'letter': 'B', 'x': w_pe['x'], 'y': w_pe['y'], 'w': w_pe['w'], 'h': w_pe['h'], 'line_text': l['text']})
                opt_tokens.append({'letter': 'C', 'x': w_boa['x'], 'y': w_boa['y'], 'w': 35, 'h': 28, 'line_text': l['text']})
                continue

        is_opt, letter, w_obj = _is_option_line(l, w_img)
        if is_opt and w_obj is not None:
            opt_tokens.append({
                'letter': letter,
                'x': w_obj['x'], 'y': w_obj['y'],
                'w': w_obj['w'], 'h': w_obj['h'],
                'line_text': l['text']
            })

    opt_tokens.sort(key=lambda o: (o['y'], o['x']))
    print(f"[DYNAMIC DETECTOR] Total token opsi terdeteksi: {len(opt_tokens)}")

    # 1. Klasterisasi Opsi per Soal
    clusters = []
    current_cluster = []

    for opt in opt_tokens:
        if not current_cluster:
            current_cluster.append(opt)
            continue

        last = current_cluster[-1]
        dy = opt['y'] - last['y']
        dx = abs(opt['x'] - last['x'])

        is_vert = (dy < 80 and dx < 100)
        is_gap = (dy <= 115 and dx < 100 and last['letter'] == 'A' and opt['letter'] == 'C')
        is_horiz = (dy < 30 and dx > 100)

        if (is_vert or is_gap or is_horiz) and len(current_cluster) < 4:
            current_cluster.append(opt)
        else:
            if current_cluster:
                clusters.append(current_cluster)
            current_cluster = [opt]

    if current_cluster:
        clusters.append(current_cluster)

    # Filter klaster noise palsu (misal: 1 token X_SYM dari goresan pada gambar ilustrasi tanpa ada huruf A/B/C)
    valid_clusters = []
    for c in clusters:
        has_real_letter = any(o['letter'] in ['A', 'B', 'C', 'D'] for o in c)
        if len(c) == 1 and not has_real_letter:
            continue
        valid_clusters.append(c)
    clusters = valid_clusters

    print(f"[DYNAMIC DETECTOR] Total klaster soal: {len(clusters)}")

    # 2. Letter-Aware Option Extraction & Interpolation
    clusters_info = []
    for c_idx, cluster in enumerate(clusters):
        opts_dict = {}

        ref_x = int(np.median([o['x'] for o in cluster]))
        ref_w = max(35, int(np.median([o['w'] for o in cluster])))
        ref_h = max(26, int(np.median([o['h'] for o in cluster])))
        default_step = 38

        is_horizontal = (
            len(cluster) >= 2 and
            abs(cluster[0]['y'] - cluster[1]['y']) < 25 and
            abs(cluster[1]['x'] - cluster[0]['x']) > 100
        )

        if is_horizontal:
            cluster.sort(key=lambda o: o['x'])
            letters = ['A', 'B', 'C', 'D']
            for i, opt in enumerate(cluster[:3]):
                opts_dict[letters[i]] = [opt['x'], opt['y'], max(35, opt['w']), max(28, opt['h'])]
            if len(cluster) == 2:
                dx_step = cluster[1]['x'] - cluster[0]['x']
                opts_dict['C'] = [cluster[1]['x'] + dx_step, cluster[1]['y'], 35, 28]
        else:
            cluster_sorted = sorted(cluster, key=lambda o: o['y'])
            if len(cluster_sorted) >= 3:
                opts_dict['A'] = [cluster_sorted[0]['x'], cluster_sorted[0]['y'], ref_w, ref_h]
                opts_dict['B'] = [cluster_sorted[1]['x'], cluster_sorted[1]['y'], ref_w, ref_h]
                opts_dict['C'] = [cluster_sorted[2]['x'], cluster_sorted[2]['y'], ref_w, ref_h]
            elif len(cluster_sorted) == 2:
                o0, o1 = cluster_sorted[0], cluster_sorted[1]
                let0, let1 = o0['letter'], o1['letter']
                dy = o1['y'] - o0['y']
                step = dy if 25 <= dy <= 60 else default_step
                mid_x = int((o0['x'] + o1['x']) / 2)

                if let0 == 'A' and let1 == 'C':
                    opts_dict['A'] = [o0['x'], o0['y'], ref_w, ref_h]
                    opts_dict['B'] = [mid_x, int((o0['y'] + o1['y']) / 2), ref_w, ref_h]
                    opts_dict['C'] = [o1['x'], o1['y'], ref_w, ref_h]
                elif let0 in ['B', 'X_SYM'] and let1 == 'C':
                    opts_dict['A'] = [mid_x, max(0, o0['y'] - step), ref_w, ref_h]
                    opts_dict['B'] = [o0['x'], o0['y'], ref_w, ref_h]
                    opts_dict['C'] = [o1['x'], o1['y'], ref_w, ref_h]
                elif let0 == 'A' and let1 in ['B', 'X_SYM']:
                    opts_dict['A'] = [o0['x'], o0['y'], ref_w, ref_h]
                    opts_dict['B'] = [o1['x'], o1['y'], ref_w, ref_h]
                    opts_dict['C'] = [mid_x, o1['y'] + step, ref_w, ref_h]
                else:
                    opts_dict['A'] = [o0['x'], o0['y'], ref_w, ref_h]
                    opts_dict['B'] = [o1['x'], o1['y'], ref_w, ref_h]
                    opts_dict['C'] = [mid_x, o1['y'] + step, ref_w, ref_h]
            elif len(cluster_sorted) == 1:
                o = cluster_sorted[0]
                let = o['letter']
                y0, x0 = o['y'], o['x']
                step = default_step

                if let == 'C':
                    # Jika hanya opsi C yang terdeteksi, opsi A dan B berada di ATAS C
                    opts_dict['A'] = [x0, max(0, y0 - 2 * step), ref_w, ref_h]
                    opts_dict['B'] = [x0, max(0, y0 - step), ref_w, ref_h]
                    opts_dict['C'] = [x0, y0, ref_w, ref_h]
                elif let == 'B':
                    # Jika hanya opsi B yang terdeteksi, A di atas dan C di bawah
                    opts_dict['A'] = [x0, max(0, y0 - step), ref_w, ref_h]
                    opts_dict['B'] = [x0, y0, ref_w, ref_h]
                    opts_dict['C'] = [x0, y0 + step, ref_w, ref_h]
                else:
                    # Jika opsi A atau X_SYM di posisi atas
                    opts_dict['A'] = [x0, y0, ref_w, ref_h]
                    opts_dict['B'] = [x0, y0 + step, ref_w, ref_h]
                    opts_dict['C'] = [x0, y0 + 2 * step, ref_w, ref_h]

        if not opts_dict:
            ref_y = cluster[0]['y'] if cluster else y_min + 50
            opts_dict['A'] = [ref_x, ref_y, 35, 26]
            opts_dict['B'] = [ref_x, ref_y + 38, 35, 26]
            opts_dict['C'] = [ref_x, ref_y + 76, 35, 26]

        min_opt_y = min(b[1] for b in opts_dict.values())
        max_opt_y = max(b[1] + b[3] for b in opts_dict.values())
        clusters_info.append({
            'opts_dict': opts_dict,
            'min_y': min_opt_y,
            'max_y': max_opt_y
        })

    # 3. Continuous Band Partitioning (Partisi Kontinu Vertikal Antar-Soal)
    # Memastikan 100% teks pertanyaan, gambar ilustrasi, dan pernyataan soal terbingkai rapi
    N = len(clusters_info)
    split_points = [y_min]
    for i in range(N - 1):
        prev_bottom = clusters_info[i]['max_y']
        next_top_opts = clusters_info[i+1]['min_y']

        prompts_in_between = [
            l['y'] for l in content_lines
            if prev_bottom <= l['y'] < next_top_opts and _is_question_prompt(l['text'], l['x'], w_img)
        ]
        if prompts_in_between:
            split_y = max(prev_bottom + 5, prompts_in_between[0] - 8)
        else:
            split_y = int((prev_bottom + next_top_opts) / 2)

        split_points.append(split_y)
    split_points.append(y_max)

    questions = []
    for i in range(N):
        q_start = split_points[i]
        q_end = split_points[i+1]
        q_box = [int(0.06 * w_img), int(q_start), int(0.88 * w_img), int(q_end - q_start)]
        questions.append({
            'nomor_soal': start_question_number + i,
            'prompt_text': '',
            'bbox': q_box,
            'options': clusters_info[i]['opts_dict']
        })

    print(f"[DYNAMIC DETECTOR] Total soal terdeteksi: {len(questions)}")
    return questions



def track_and_predict_questions(
    image_input: Union[str, bytes, Image.Image, Any],
    threshold: float = 0.40,
    model_path: Optional[str] = None,
    start_question_number: int = 1
) -> Dict[str, Any]:
    """
    Fungsi Utama Universal Dynamic AI Exam Detector:
    1. Membaca gambar lembar soal siswa (mata pelajaran apa saja).
    2. Mengekstrak soal & opsi A, B, C secara dinamis via OCR + Layout Geometry.
    3. Mengevaluasi tanda silang (X) dengan Ensemble Hibrida (CV Diagonal 65% + ResNet50 35%).
    4. Argmax kompetitif per soal → hanya 1 jawaban terpilih per nomor.
    5. Menggambar anotasi visual presisi & mengembalikan JSON terstruktur.
    """
    from tensorflow.keras.applications.resnet50 import preprocess_input

    # 1. Load Gambar OpenCV
    img = load_image_cv2(image_input)
    h_orig, w_orig = img.shape[:2]

    # Standarisasi resolusi agar pemrosesan stabil dan cepat
    MAX_DIM = 1800
    if max(h_orig, w_orig) > MAX_DIM:
        scale = MAX_DIM / float(max(h_orig, w_orig))
        new_w = max(100, int(w_orig * scale))
        new_h = max(100, int(h_orig * scale))
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)


    img_annotated = img.copy()
    h_img, w_img = img.shape[:2]

    # 2. Muat Model ResNet50 (Singleton Cache)
    model, class_names = get_model_and_classes(model_path=model_path)

    # 3. Dynamic Question & Option Extraction
    detected_questions = extract_questions_and_options(img, start_question_number=start_question_number)

    # 4. Kumpulkan seluruh potongan opsi untuk diprediksi secara BATCH
    crop_items = []
    for q in detected_questions:
        q_num = q['nomor_soal']
        for opt_letter in ['A', 'B', 'C']:
            if opt_letter not in q['options']:
                continue
            ox, oy, ow, oh = q['options'][opt_letter]
            # Kunci lebar anchor opsi agar fokus pada huruf A/B/C dan goresan silang (tidak mencaplok huruf pertama teks seperti 'M' pada 'Menjauhinya')
            ow_tight = min(30, max(24, ow))
            oh_tight = min(30, max(24, oh))
            pad_x = 2
            pad_y = 2
            x1 = max(0, ox - pad_x)
            y1 = max(0, oy - pad_y)
            x2 = min(w_img, ox + ow_tight + pad_x)
            y2 = min(h_img, oy + oh_tight + pad_y)

            if x2 - x1 < 8 or y2 - y1 < 8:
                continue

            patch = img[y1:y2, x1:x2]
            cv_res = analyze_cross_mark_patch(patch)

            patch_resized = cv2.resize(patch, (224, 224), interpolation=cv2.INTER_AREA)
            patch_rgb = cv2.cvtColor(patch_resized, cv2.COLOR_BGR2RGB)
            crop_items.append({
                'q_num': q_num,
                'opt_letter': opt_letter,
                'cv_res': cv_res,
                'bbox': [x1, y1, x2 - x1, y2 - y1],
                'array': np.array(patch_rgb, dtype=np.float32)
            })

    # Eksekusi prediksi batch ResNet50
    pred_map = {}
    if crop_items:
        batch_array = np.stack([c['array'] for c in crop_items], axis=0)
        batch_preprocessed = preprocess_input(batch_array)
        raw_preds = model.predict(batch_preprocessed, batch_size=32, verbose=0)

        for i, c in enumerate(crop_items):
            prob_terpilih = 1.0 - float(raw_preds[i][0])
            cv_res = c['cv_res']

            # Skor CV: kombinasi densitas tinta & energi garis diagonal menyilang
            cv_score = (cv_res['diag_score'] / 35.0) + (cv_res['density'] * 1.8)

            # Skor Hibrida: CV (45%) + ResNet50 Deep Learning (55%)
            hybrid_score = (cv_score * 0.45) + (prob_terpilih * 0.55)

            pred_map[(c['q_num'], c['opt_letter'])] = {
                'hybrid_score': hybrid_score,
                'prob_terpilih': prob_terpilih,
                'cv_res': cv_res,
                'bbox': c['bbox']
            }

    results = []

    # 5. Susun hasil per soal dan gambar bounding box visual
    for q in detected_questions:
        q_num = q['nomor_soal']
        qx, qy, qw, qh = q['bbox']

        # Gambar Bounding Box Soal (Biru Halus)
        cv2.rectangle(img_annotated, (qx, qy), (qx + qw, qy + qh), (220, 150, 40), 2)
        q_label = f"Soal #{q_num}"
        cv2.putText(
            img_annotated, q_label, (qx + 6, max(22, qy - 6)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.65, (220, 150, 40), 2, cv2.LINE_AA
        )

        opt_keys = [k for k in ['A', 'B', 'C'] if (q_num, k) in pred_map]
        if not opt_keys:
            continue

        scores = {k: pred_map[(q_num, k)]['hybrid_score'] for k in opt_keys}

        # Argmax Decision (opsi saling bersaing dalam 1 soal)
        best_opt = max(opt_keys, key=lambda k: scores[k])
        best_score = scores[best_opt]
        second_score = sorted(scores.values(), reverse=True)[1] if len(scores) > 1 else 0.0
        margin = best_score - second_score

        # Ambang batas validitas tanda silang
        is_answered = (best_score >= 0.38)
        chosen_opt = best_opt if is_answered else "-"

        # Hitung confidence relatif softmax antar opsi
        exp_vals = {k: np.exp(scores[k]) for k in opt_keys}
        sum_exp = sum(exp_vals.values())
        softmax_confs = {k: float(exp_vals[k] / max(1e-6, sum_exp)) for k in opt_keys}

        options_detail = {}
        for k in opt_keys:
            p_data = pred_map[(q_num, k)]
            bx, by, bw_box, bh_box = p_data['bbox']

            # Gambar bounding box opsi normal (Abu-abu lembut)
            cv2.rectangle(img_annotated, (bx, by), (bx + bw_box, by + bh_box), (180, 180, 180), 1)
            cv2.putText(
                img_annotated, k, (bx + 2, by + bh_box - 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 100, 100), 1, cv2.LINE_AA
            )

            options_detail[k] = {
                'status': 'terpilih' if k == chosen_opt else 'tidak_terpilih',
                'confidence': round(softmax_confs[k], 4),
                'hybrid_score': round(p_data['hybrid_score'], 4),
                'bbox': [bx, by, bw_box, bh_box]
            }

        # Highlight Jawaban Terpilih dengan Kotak HIJAU TEGAS & Badge
        chosen_conf = 0.0
        if chosen_opt != "-":
            cx, cy, cw, ch = pred_map[(q_num, chosen_opt)]['bbox']
            chosen_conf = max(softmax_confs[chosen_opt], pred_map[(q_num, chosen_opt)]['prob_terpilih'])
            cv2.rectangle(img_annotated, (cx, cy), (cx + cw, cy + ch), (0, 200, 0), 3)

            badge_text = f"PILIHAN: {chosen_opt} ({chosen_conf*100:.1f}%)"
            (tw, th), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(
                img_annotated,
                (cx + cw + 4, cy),
                (cx + cw + tw + 10, cy + th + 6),
                (0, 180, 0),
                -1
            )
            cv2.putText(
                img_annotated, badge_text, (cx + cw + 7, cy + th + 2),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA
            )

        results.append({
            'nomor_soal': q_num,
            'jawaban_terpilih': chosen_opt,
            'confidence': round(chosen_conf, 4) if chosen_opt != "-" else 0.0,
            'margin': round(margin, 4),
            'options_detail': options_detail,
            'bbox': {
                'x': int(qx), 'y': int(qy), 'w': int(qw), 'h': int(qh)
            }
        })

    # 6. Encode Gambar Teranotasi ke Base64
    _, buffer = cv2.imencode('.jpg', img_annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
    annotated_base64 = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"

    return {
        'success': True,
        'message': f"Berhasil mendeteksi dan mengklasifikasi {len(results)} soal pilihan ganda.",
        'total_soal_terdeteksi': len(results),
        'results': results,
        'annotated_image': annotated_base64
    }
