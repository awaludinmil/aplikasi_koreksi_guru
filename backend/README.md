# Skripsi OCR Backend (Flask)

Ini adalah *backend* untuk aplikasi penilaian esai otomatis menggunakan Flask dan MySQL.

## Persyaratan Sistem
- Python 3.10+
- MySQL Server (XAMPP / MySQL Installer)
- Git (opsional)

## Cara Menjalankan (Development)

### 1. Persiapan Database
Pastikan MySQL server Anda (misalnya melalui XAMPP) sudah berjalan.
Buat database bernama `skripsi_ocr` (atau sesuai konfigurasi Anda).

### 2. Setup Virtual Environment & Dependensi
Buka terminal (rekomendasi: Command Prompt atau PowerShell), lalu jalankan perintah berikut:

```bash
# Pindah ke direktori backend
cd backend

# Membuat virtual environment (jika belum ada)
python -m venv venv

# Mengaktifkan virtual environment (Wajib dilakukan setiap kali membuka terminal baru)
# Untuk Windows (PowerShell):
.\venv\Scripts\activate
# Untuk Windows (Command Prompt):
.\venv\Scripts\activate.bat
# Untuk Mac/Linux:
source venv/bin/activate

# Instalasi semua library yang dibutuhkan
pip install -r requirements.txt
```

*(Tanda bahwa virtual environment sudah aktif adalah munculnya tulisan `(venv)` di sebelah kiri prompt terminal Anda).*

### 3. Konfigurasi Environment Variables
Buat file bernama `.env` di dalam folder `backend` (sejajar dengan file `run.py`). Isi dengan konfigurasi berikut:

```env
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=kunci-rahasia-app-anda
JWT_SECRET_KEY=kunci-rahasia-jwt-anda

# URL Koneksi Database MySQL
# Format: mysql+pymysql://username:password@localhost/nama_database
DATABASE_URL=mysql+pymysql://root:@127.0.0.1/skripsi_ocr
```

### 4. Migrasi Database (Opsional jika tabel belum ada)
Jika Anda baru pertama kali menjalankan aplikasi dan tabel belum dibuat:
```bash
flask db upgrade
```

### 5. Menjalankan Server
Pastikan virtual environment masih aktif `(venv)`, lalu jalankan:
```bash
flask run
# ATAU
python run.py
```
Server akan berjalan di `http://127.0.0.1:5000/`.

---

## Struktur Folder Utama
- `app/` - Source code utama Flask (Routes, Models, Config).
- `migrations/` - File migrasi database Flask-Migrate.
- `venv/` - Lingkungan virtual Python (tidak di-commit ke Git).
- `.env` - Konfigurasi rahasia.
- `run.py` - Entry point aplikasi.
