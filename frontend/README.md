# Skripsi OCR Frontend (Flutter)

Aplikasi *mobile* berbasis Flutter untuk membantu guru mengoreksi ujian secara otomatis. Terintegrasi dengan backend Flask.

## Persyaratan Sistem
- Flutter SDK (versi 3.10.x atau lebih baru disarankan)
- Android Studio / VS Code dengan ekstensi Flutter
- Emulator Android / Perangkat Fisik Android / Google Chrome (untuk Web)

## Cara Menjalankan

### 1. Instalasi Dependensi
Buka terminal dan arahkan ke folder `frontend`, lalu unduh semua _package_ yang dibutuhkan:
```bash
cd frontend
flutter pub get
```

### 2. Konfigurasi URL API Backend (Sangat Penting!)
Aplikasi Flutter perlu tahu di mana letak _backend_ Flask Anda.
Buka file `lib/config/app_constants.dart`.

```dart
class AppConstants {
  // Jika menggunakan Android Emulator (Backend berjalan di localhost PC):
  static const String apiBaseUrl = 'http://10.0.2.2:5000/api/v1';

  // Jika menggunakan Perangkat HP Fisik atau Web (Backend dan HP harus satu WiFi):
  // Ganti IP di bawah ini dengan IP Address PC Anda (IPv4), contoh:
  // static const String apiBaseUrl = 'http://192.168.1.10:5000/api/v1';
}
```

### 3. Menjalankan Aplikasi
Pilih perangkat tujuan (Emulator/Chrome) di editor Anda, lalu jalankan:
```bash
flutter run
```

---

## Fitur Logging (Dio)
Aplikasi ini menggunakan _package_ `dio` untuk koneksi HTTP. Kami telah mengaktifkan `LogInterceptor`, sehingga Anda dapat memantau aktivitas jaringan (Request URL, Headers, Body, dan Response) secara langsung melalui **Debug Console** di VS Code atau terminal tempat Anda menjalankan `flutter run`. Ini akan sangat memudahkan proses pencarian _bug_ (debugging).

## Struktur Folder Utama
- `lib/app/` - Pengaturan rute (Routes) dan navigasi awal.
- `lib/config/` - Tema warna, gaya teks, dan konstanta global.
- `lib/data/` - Model JSON dan Service API (ApiClient).
- `lib/providers/` - State Management (seperti status Login).
- `lib/screens/` - Halaman antarmuka UI utama.
- `lib/widgets/` - Komponen UI kecil yang bisa digunakan berulang kali.
