import 'package:flutter/material.dart';

class AppColors {
  // Primary (Axolotl Pink mapped to Red for "merah putih" vibe as requested)
  // Axolotl Pink Tint/Shade Scale (100-900)
  static const Color axolotlPink = Color(0xFFFF6B9D);
  static const Color axolotlPink100 = Color(0xFFFFF0F5);
  static const Color axolotlPink300 = Color(0xFFFFADC9);
  static const Color axolotlPink700 = Color(0xFFA81F4D);
  static const Color axolotlPink900 = Color(0xFF500F26);
  
  static const Color deepTeal = Color(0xFF0F766E);
  
  // Neutral Palette (Slate scale)
  static const Color slate950 = Color(0xFF0B1120);
  static const Color slate700 = Color(0xFF334155);
  static const Color slate500 = Color(0xFF64748B);
  static const Color slate300 = Color(0xFFCBD5E1);
  static const Color slate100 = Color(0xFFF1F5F9);
  
  static const Color white = Color(0xFFFFFFFF);
  
  // Semantic Palette
  static const Color success = Color(0xFF22C55E);
  static const Color warning = Color(0xFFF59E0B);
  static const Color error = Color(0xFFEF4444);
  static const Color info = Color(0xFF3B82F6);
  
  // App Theme aliases ("Merah Putih" theme request)
  static const Color merahIndo = Color(0xFFEF4444); // Using a pleasant red instead of pure FF0000 for better UI
  
  static const Color primary = merahIndo; // User requested "warnanya merah putih"
  static const Color primaryAccent = axolotlPink;
  static const Color secondary = deepTeal;
  
  static const Color background = slate100;
  static const Color surface = white;
  static const Color textPrimary = slate950;
  static const Color textSecondary = slate700;
  static const Color textMuted = slate500;
  static const Color border = slate300;
}
