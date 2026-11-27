import 'package:flutter/material.dart';
import '../../config/app_colors.dart';
import '../../config/app_text_styles.dart';

class OcrResultRow extends StatelessWidget {
  final int no;
  final String jwbSiswa;
  final String kunciJwb;
  final bool isBenar;
  final bool isEven;
  final VoidCallback onTap;

  const OcrResultRow({
    super.key,
    required this.no,
    required this.jwbSiswa,
    required this.kunciJwb,
    required this.isBenar,
    required this.onTap,
    this.isEven = false,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        color: isEven ? AppColors.slate100 : AppColors.surface,
        child: Row(
          children: [
            Expanded(flex: 1, child: Text(no.toString(), style: AppTextStyles.bodyText)),
            Expanded(flex: 2, child: Text(jwbSiswa, style: AppTextStyles.bodyText.copyWith(fontWeight: FontWeight.bold))),
            Expanded(flex: 2, child: Text(kunciJwb, style: AppTextStyles.bodyText)),
            Expanded(
              flex: 2,
              child: Row(
                children: [
                  Icon(
                    isBenar ? Icons.check_circle : Icons.cancel, 
                    color: isBenar ? AppColors.success : AppColors.error,
                    size: 16,
                  ),
                  const SizedBox(width: 4),
                  Text(
                    isBenar ? 'Benar' : 'Salah', 
                    style: AppTextStyles.bodyText.copyWith(
                      color: isBenar ? AppColors.success : AppColors.error
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
