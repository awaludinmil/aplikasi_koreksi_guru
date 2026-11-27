import 'package:flutter/foundation.dart';

class AppConstants {
  static const String appName = 'Aplikasi Guru';

  // ─── Backend API ───────────────────────────────────────────────────
  // Dinamis mendeteksi platform agar tidak perlu ubah IP manual
  static String get _host {
    if (kIsWeb) {
      return '127.0.0.1'; // Untuk Chrome / Web
    } else if (defaultTargetPlatform == TargetPlatform.android) {
      return '10.0.2.2'; // Untuk Emulator Android
    } else {
      return '127.0.0.1'; // Untuk Windows Desktop / iOS Simulator
    }
  }
  
  static const int _port = 5000;
  static String get apiBaseUrl => 'http://$_host:$_port/api';

  // ─── Padding & Margin ──────────────────────────────────────────────
  static const double paddingSmall = 8.0;
  static const double paddingNormal = 16.0;
  static const double paddingLarge = 24.0;

  // ─── Border Radius ─────────────────────────────────────────────────
  static const double radiusSmall = 4.0;
  static const double radiusNormal = 8.0;
  static const double radiusLarge = 12.0;
}
