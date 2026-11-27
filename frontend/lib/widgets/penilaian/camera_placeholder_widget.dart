import 'dart:typed_data';
import 'package:flutter/material.dart';
import '../../config/app_colors.dart';
import '../../config/app_text_styles.dart';
import '../../config/app_constants.dart';
import '../common/custom_button.dart';

class CameraPlaceholderWidget extends StatelessWidget {
  final List<Map<String, dynamic>> images;
  final VoidCallback onCameraTap;
  final VoidCallback onGalleryTap;
  final Function(int) onRemoveTap;

  const CameraPlaceholderWidget({
    super.key,
    required this.images,
    required this.onCameraTap,
    required this.onGalleryTap,
    required this.onRemoveTap,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        if (images.isNotEmpty) ...[
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(AppConstants.radiusNormal),
              border: Border.all(color: AppColors.border, width: 1.5),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.check_circle, color: AppColors.success, size: 20),
                    const SizedBox(width: 8),
                    Text(
                      '${images.length}/4 Foto Terpilih',
                      style: AppTextStyles.h3.copyWith(color: AppColors.success),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                SizedBox(
                  height: 120,
                  child: ListView.builder(
                    scrollDirection: Axis.horizontal,
                    itemCount: images.length,
                    itemBuilder: (context, index) {
                      final imageData = images[index];
                      return Container(
                        width: 90,
                        margin: const EdgeInsets.only(right: 12),
                        child: Stack(
                          children: [
                            ClipRRect(
                              borderRadius: BorderRadius.circular(8),
                              child: Image.memory(
                                imageData['bytes'] as Uint8List,
                                height: 120,
                                width: 90,
                                fit: BoxFit.cover,
                              ),
                            ),
                            Positioned(
                              top: -4,
                              right: -4,
                              child: IconButton(
                                icon: Container(
                                  decoration: const BoxDecoration(
                                    color: Colors.white,
                                    shape: BoxShape.circle,
                                  ),
                                  child: const Icon(Icons.cancel, color: AppColors.error, size: 24),
                                ),
                                onPressed: () => onRemoveTap(index),
                              ),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
        ],

        if (images.length < 4) ...[
          Container(
            height: 120,
            width: double.infinity,
            decoration: BoxDecoration(
              color: AppColors.slate100,
              borderRadius: BorderRadius.circular(AppConstants.radiusNormal),
              border: Border.all(color: AppColors.border, style: BorderStyle.solid),
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: const [
                Icon(Icons.add_a_photo, size: 32, color: AppColors.slate300),
                SizedBox(height: 8),
                Text('Tambah Foto Lembar Jawaban', style: AppTextStyles.bodyText),
                Text('Maks: 4 Gambar', style: AppTextStyles.bodyTextSmall),
              ],
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: CustomButton(
                  text: 'Ambil Foto',
                  isOutlined: true,
                  onPressed: onCameraTap,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: CustomButton(
                  text: 'Pilih Galeri',
                  isOutlined: true,
                  onPressed: onGalleryTap,
                ),
              ),
            ],
          ),
        ],
      ],
    );
  }
}
