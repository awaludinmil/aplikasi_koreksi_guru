"""
================================================================================
Test Verifikasi End-to-End Detector Lembar Soal (app.utils.detector)
================================================================================
"""

import os
import io
import cv2
from app.utils.detector import track_and_predict_questions
from app import create_app

def run_e2e_test():
    img_dir = r'..\foto bru'
    files = [
        ('WhatsApp Image 2026-10-20 at 16.14.01.jpeg', 1, range(1, 6)),
        ('WhatsApp Image 2026-10-20 at 16.14.00 (1).jpeg', 2, range(6, 14)),
        ('WhatsApp Image 2026-10-20 at 16.14.00.jpeg', 3, range(14, 16)),
    ]

    expected_answers = {
        1: 'B', 2: 'A', 3: 'C', 4: 'B', 5: 'A',
        6: 'C', 7: 'B', 8: 'C', 9: 'B', 10: 'A', 11: 'A', 12: 'A', 13: 'B',
        14: 'C', 15: 'B'
    }

    print("=" * 70)
    print("MEMULAI PENGUJIAN END-TO-END PIPELINE DETECTOR TERBARU")
    print("=" * 70)

    total_correct = 0
    total_tested = 15
    all_results = []

    current_offset = 0
    for fname, page_num, expected_range in files:
        p = os.path.join(img_dir, fname)
        print(f"\n>> Memproses {fname} (Target: Halaman {page_num})...")
        res = track_and_predict_questions(p)
        
        assert res['success'] is True, "Hasil harus success=True"
        soal_list = res['results']
        print(f"   Jumlah soal terdeteksi: {len(soal_list)} soal.")
        
        for s in soal_list:
            global_q_num = current_offset + s['nomor_soal']
            ans = s['jawaban_terpilih']
            exp = expected_answers.get(global_q_num, '?')
            is_match = (ans == exp)
            if is_match:
                total_correct += 1
            status = "PASS" if is_match else "FAIL"
            print(f"   - Soal #{global_q_num:2d} (Hal {page_num} #{s['nomor_soal']}): Jawaban={ans} (Expected: {exp}) [{status}] conf={s['confidence']*100:.1f}%")
            all_results.append(s)
        current_offset += len(soal_list)


    print("\n" + "=" * 70)
    print(f"TOTAL AKURASI DETEKSI: {total_correct}/{total_tested} ({total_correct/total_tested*100:.1f}%)")
    print("=" * 70)

    # Uji via Flask Test Client (Multi-image upload)
    print("\n>> Menguji Endpoint API /api/assesment/predict via Flask Test Client...")
    app = create_app()
    client = app.test_client()

    data = {}
    data['threshold'] = '0.40'
    files_to_send = []
    
    for fname, _, _ in files:
        p = os.path.join(img_dir, fname)
        with open(p, 'rb') as fp:
            files_to_send.append((io.BytesIO(fp.read()), fname))

    data['images'] = files_to_send
    
    resp = client.post(
        '/api/assesment/predict',
        data=data,
        content_type='multipart/form-data'
    )

    print(f"   Status Code API: {resp.status_code}")
    json_resp = resp.get_json()
    assert resp.status_code == 200, f"API Error: {json_resp}"
    print(f"   Total Soal API: {json_resp.get('total_soal_terdeteksi')}")
    print(f"   Total Gambar Anotasi: {len(json_resp.get('annotated_images', []))}")
    print("\n[SUKSES] Seluruh pengujian pipeline & API berhasil!")

if __name__ == '__main__':
    run_e2e_test()
