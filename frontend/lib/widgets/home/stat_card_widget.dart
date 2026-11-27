import 'package:flutter/material.dart';
import '../../config/app_colors.dart';
import '../../config/app_text_styles.dart';
import '../../config/app_constants.dart';

class StatCardWidget extends StatelessWidget {
  final IconData icon;
  final String value;
  final String label;

  const StatCardWidget({
    super.key,
    required this.icon,
    required this.value,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(AppConstants.radiusNormal),
        border: Border.all(color: AppColors.border),
        boxShadow: [
          BoxShadow(
            color: AppColors.slate950.withOpacity(0.05),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        children: [
          Icon(icon, size: 32, color: AppColors.secondary),
          const SizedBox(height: 8),
          Text(value, style: AppTextStyles.h1),
          const SizedBox(height: 4),
          Text(
            label, 
            style: AppTextStyles.bodyTextSmall,
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}
