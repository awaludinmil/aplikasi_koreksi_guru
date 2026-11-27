import 'package:flutter/material.dart';
import '../../config/app_colors.dart';
import '../../config/app_text_styles.dart';

class RecentAssesmentCard extends StatelessWidget {
  final String nama;
  final String mapel;
  final String nilai;
  final String status;
  final bool isFinished;
  final bool isEven;

  const RecentAssesmentCard({
    super.key,
    required this.nama,
    required this.mapel,
    required this.nilai,
    required this.status,
    required this.isFinished,
    this.isEven = false,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      color: isEven ? AppColors.slate100 : AppColors.surface,
      child: Row(
        children: [
          Expanded(flex: 2, child: Text(nama, style: AppTextStyles.bodyText)),
          Expanded(flex: 2, child: Text(mapel, style: AppTextStyles.bodyText)),
          Expanded(flex: 1, child: Text(nilai, style: AppTextStyles.bodyText)),
          Expanded(
            flex: 2, 
            child: Row(
              children: [
                Icon(
                  isFinished ? Icons.check_circle : Icons.pending, 
                  color: isFinished ? AppColors.success : AppColors.warning,
                  size: 16,
                ),
                const SizedBox(width: 4),
                Text(status, style: AppTextStyles.bodyText),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
