"""
OCR Utility — Sistem Penilaian Jawaban Siswa
=============================================

Modul ini bertanggung jawab memproses gambar lembar jawaban siswa
dan mengekstrak jawaban per nomor soal (A/B/C/D).

Saat ini menggunakan MODE STUB/DUMMY untuk keperluan development.
Untuk mengaktifkan OCR sungguhan (Tesseract), ubah USE_REAL_OCR = True
dan pastikan Tesseract sudah terinstall di sistem.

Instalasi Tesseract (Windows):
  https://github.com/UB-Mannheim/tesseract/wiki
  Lalu tambahkan ke PATH atau set TESSERACT_CMD di .env

Alternatif: Ganti fungsi _ocr_with_tesseract() dengan model ML custom (YOLO, CNN, dll.)
"""

import os
import random
from typing import Tuple, List, Dict

# Ubah ke True jika Tesseract sudah terinstall
USE_REAL_OCR = os.getenv('USE_REAL_OCR', 'false').lower() == 'true'

VALID_CHOICES = ['A', 'B', 'C', 'D']


def process_ocr_image(image_file, jumlah_soal: int = 10) -> Tuple[List[Dict], bool]:
    """
    Proses gambar lembar jawaban siswa dan kembalikan hasil per soal.

    Args:
        image_file : FileStorage (Flask) — gambar JPG/PNG lembar jawaban
        jumlah_soal : jumlah soal yang perlu dideteksi

    Returns:
        Tuple:
          - List[Dict] : [{ "nomor_soal": 1, "jawaban_siswa": "A" }, ...]
          - bool       : True jika menggunakan dummy/stub
    """
    if USE_REAL_OCR:
        try:
            result = _ocr_with_tesseract(image_file, jumlah_soal)
            return result, False
        except Exception as e:
            print(f'[OCR WARNING] Tesseract gagal, fallback ke dummy: {e}')
            return _ocr_dummy(jumlah_soal), True
    else:
        return _ocr_dummy(jumlah_soal), True


def _ocr_dummy(jumlah_soal: int) -> List[Dict]:
    """
    Mode STUB — return jawaban simulasi acak (A/B/C/D).
    Digunakan saat Tesseract belum terpasang atau USE_REAL_OCR=false.
    Guru dapat mengedit hasilnya secara manual di aplikasi.
    """
    return [
        {
            'nomor_soal': i,
            'jawaban_siswa': random.choice(VALID_CHOICES),
        }
        for i in range(1, jumlah_soal + 1)
    ]


def _ocr_with_tesseract(image_file, jumlah_soal: int) -> List[Dict]:
    """
    Mode OCR SUNGGUHAN menggunakan pytesseract.
    Membutuhkan:
      - Tesseract terinstall di sistem
      - pytesseract dan Pillow terinstall (ada di requirements.txt)

    Strategi saat ini: ekstrak semua teks dari gambar dan parse pilihan A/B/C/D.
    Untuk akurasi lebih baik, implementasikan deteksi bubble sheet / OMR.
    """
    import pytesseract
    from PIL import Image

    # Path Tesseract (Windows) — bisa diset via env variable
    tesseract_cmd = os.getenv('TESSERACT_CMD', r'C:\Program Files\Tesseract-OCR\tesseract.exe')
    if os.name == 'nt' and os.path.exists(tesseract_cmd):
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    # Buka gambar
    img = Image.open(image_file)

    # Pre-processing: konversi ke grayscale untuk akurasi lebih baik
    img = img.convert('L')

    # Ekstrak teks
    raw_text = pytesseract.image_to_string(img, config='--psm 6')

    # Parse hasil teks — cari pola "1. A", "2) B", "No 3 C", dll.
    result = _parse_ocr_text(raw_text, jumlah_soal)
    return result


def _parse_ocr_text(raw_text: str, jumlah_soal: int) -> List[Dict]:
    """
    Parse teks mentah dari Tesseract untuk mengekstrak jawaban per soal.
    Fallback ke '-' jika tidak bisa dideteksi.
    """
    import re

    lines = raw_text.strip().split('\n')
    jawaban_map: Dict[int, str] = {}

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Cari pola: nomor diikuti jawaban (A/B/C/D)
        # Contoh: "1. A", "1) A", "1 A", "No.1 A"
        match = re.search(r'(\d+)[.):\s]+([ABCDE])\b', line.upper())
        if match:
            nomor = int(match.group(1))
            jawaban = match.group(2)
            if 1 <= nomor <= jumlah_soal:
                jawaban_map[nomor] = jawaban

    # Susun hasil untuk semua nomor soal
    return [
        {
            'nomor_soal': i,
            'jawaban_siswa': jawaban_map.get(i, '-'),  # '-' jika tidak terdeteksi
        }
        for i in range(1, jumlah_soal + 1)
    ]
