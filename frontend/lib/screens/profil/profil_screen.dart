import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../config/app_text_styles.dart';
import '../../config/app_constants.dart';
import '../../config/app_colors.dart';
import '../../widgets/common/custom_button.dart';
import '../../app/routes.dart';
import '../../app/auth_provider.dart';

class ProfilScreen extends StatelessWidget {
  const ProfilScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final user = context.watch<AuthProvider>().user;
    
    return SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(AppConstants.paddingLarge),
        child: Column(
          children: [
            const Text('Profil Akun Guru', style: AppTextStyles.h1),
            const SizedBox(height: 32),
            
            const CircleAvatar(
              radius: 50,
              backgroundColor: AppColors.slate300,
              child: Icon(Icons.person, size: 50, color: AppColors.white),
            ),
            const SizedBox(height: 16),
            Text(user?.namaLengkap ?? '-', style: AppTextStyles.h2),
            Text('@${user?.username ?? '-'}', style: AppTextStyles.bodyTextSmall),
            
            const SizedBox(height: 32),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                border: Border.all(color: AppColors.border),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Informasi Akun', style: AppTextStyles.h3),
                  const Divider(),
                  const SizedBox(height: 8),
                  const Text('Nama Lengkap', style: AppTextStyles.bodyTextSmall),
                  Text(user?.namaLengkap ?? '-', style: AppTextStyles.bodyText),
                  const SizedBox(height: 16),
                  const Text('Username', style: AppTextStyles.bodyTextSmall),
                  Text(user?.username ?? '-', style: AppTextStyles.bodyText),
                ],
              ),
            ),
            const SizedBox(height: 32),
            
            CustomButton(
              text: 'LOGOUT',
              isOutlined: true,
              onPressed: () async {
                await context.read<AuthProvider>().logout();
                if (context.mounted) {
                  Navigator.pushNamedAndRemoveUntil(context, AppRoutes.login, (route) => false);
                }
              },
            ),
          ],
        ),
      ),
    );
  }
}
