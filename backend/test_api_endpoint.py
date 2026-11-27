import os
import requests
import json

sample_image = os.path.abspath(r'..\WhatsApp Image 2026-09-03 at 17.18.35.jpeg')
url = "http://127.0.0.1:5000/api/assesment/predict"
print(f"Testing live API: {url} with image {sample_image}...")

with open(sample_image, "rb") as f:
    files = {"images": ("17.18.35.jpeg", f, "image/jpeg")}
    data = {"threshold": "0.40"}
    response = requests.post(url, files=files, data=data)

print(f"Status Code: {response.status_code}")
try:
    res_json = response.json()
    print("Response JSON summary:")
    print(f"  Success: {res_json.get('success')}")
    print(f"  Total Soal Terdeteksi: {res_json.get('total_soal_terdeteksi')}")
    print("\n  Daftar Hasil:")
    for r in res_json.get('results', []):
        print(f"    - Soal #{r.get('nomor_soal')}: Jawaban=[{r.get('jawaban_terpilih')}] (Conf: {r.get('confidence')})")
    print(f"  Annotated Images count: {len(res_json.get('annotated_images', []))}")
except Exception as e:
    print("Response text:", response.text)
