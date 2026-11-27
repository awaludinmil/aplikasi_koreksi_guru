import 'package:flutter/material.dart';
import '../../config/app_text_styles.dart';
import '../../config/app_constants.dart';
import '../../config/app_colors.dart';
import '../../widgets/common/custom_text_field.dart';
import '../../widgets/common/custom_button.dart';

import 'package:provider/provider.dart';
import '../../app/auth_provider.dart';
import '../../app/routes.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _namaController = TextEditingController();
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmController = TextEditingController();
  bool _isLoading = false;

  void _register() async {
    if (_formKey.currentState!.validate()) {
      setState(() => _isLoading = true);
      
      final auth = context.read<AuthProvider>();
      final success = await auth.register(
        namaLengkap: _namaController.text,
        username: _usernameController.text,
        password: _passwordController.text,
        confirmPassword: _confirmController.text,
      );
      
      if (mounted) {
        setState(() => _isLoading = false);
        if (success) {
          // Register otomatis login, arahkan ke MainLayout
          Navigator.pushNamedAndRemoveUntil(context, AppRoutes.mainLayout, (route) => false);
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(auth.errorMessage ?? 'Gagal daftar'),
              backgroundColor: AppColors.error,
            ),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(AppConstants.paddingLarge),
            child: Form(
              key: _formKey,
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Text(
                    'BUAT AKUN BARU',
                    style: AppTextStyles.h1,
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 10),
                  const Divider(color: AppColors.textPrimary, thickness: 1),
                  const SizedBox(height: 30),
                  
                  CustomTextField(
                    label: 'Nama Lengkap',
                    controller: _namaController,
                    validator: (val) => val == null || val.isEmpty ? 'Wajib diisi' : null,
                  ),
                  const SizedBox(height: AppConstants.paddingNormal),
                  
                  CustomTextField(
                    label: 'Username',
                    controller: _usernameController,
                    validator: (val) => val == null || val.isEmpty ? 'Wajib diisi' : null,
                  ),
                  const SizedBox(height: AppConstants.paddingNormal),
                  
                  CustomTextField(
                    label: 'Password',
                    isPassword: true,
                    controller: _passwordController,
                    validator: (val) => val == null || val.isEmpty ? 'Wajib diisi' : null,
                  ),
                  const SizedBox(height: AppConstants.paddingNormal),

                  CustomTextField(
                    label: 'Konfirmasi Password',
                    isPassword: true,
                    controller: _confirmController,
                    validator: (val) {
                      if (val == null || val.isEmpty) return 'Wajib diisi';
                      if (val != _passwordController.text) return 'Password tidak cocok';
                      return null;
                    },
                  ),
                  const SizedBox(height: 30),
                  
                  CustomButton(
                    text: 'Daftar',
                    isLoading: _isLoading,
                    onPressed: _register,
                  ),
                  const SizedBox(height: 30),
                  
                  Row(
                    children: const [
                      Expanded(child: Divider(color: AppColors.textPrimary)),
                      Padding(
                        padding: EdgeInsets.symmetric(horizontal: 16),
                        child: Text('atau', style: AppTextStyles.bodyTextSmall),
                      ),
                      Expanded(child: Divider(color: AppColors.textPrimary)),
                    ],
                  ),
                  const SizedBox(height: 30),
                  
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Text('Sudah Punya Akun? ', style: AppTextStyles.bodyText),
                      GestureDetector(
                        onTap: () => Navigator.pop(context),
                        child: const Text('Masuk Disini', style: AppTextStyles.linkText),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
