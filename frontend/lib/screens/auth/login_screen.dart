import 'package:flutter/material.dart';
import '../../config/app_text_styles.dart';
import '../../config/app_constants.dart';
import '../../config/app_colors.dart';
import '../../widgets/common/custom_text_field.dart';
import '../../widgets/common/custom_button.dart';
import '../../app/routes.dart';

import 'package:provider/provider.dart';
import '../../app/auth_provider.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isLoading = false;

  void _login() async {
    if (_formKey.currentState!.validate()) {
      setState(() => _isLoading = true);
      
      final auth = context.read<AuthProvider>();
      final success = await auth.login(
        _usernameController.text,
        _passwordController.text,
      );
      
      if (mounted) {
        setState(() => _isLoading = false);
        if (success) {
          Navigator.pushReplacementNamed(context, AppRoutes.mainLayout);
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(auth.errorMessage ?? 'Gagal login'),
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
                    'SELAMAT DATANG KEMBALI!',
                    style: AppTextStyles.h1,
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 10),
                  const Divider(color: AppColors.textPrimary, thickness: 1),
                  const SizedBox(height: 40),
                  
                  CustomTextField(
                    label: 'Username',
                    controller: _usernameController,
                    validator: (val) => val == null || val.isEmpty ? 'Username tidak boleh kosong' : null,
                  ),
                  const SizedBox(height: AppConstants.paddingNormal),
                  
                  CustomTextField(
                    label: 'Password',
                    isPassword: true,
                    controller: _passwordController,
                    validator: (val) => val == null || val.isEmpty ? 'Password tidak boleh kosong' : null,
                  ),
                  const SizedBox(height: 40),
                  
                  CustomButton(
                    text: 'MASUK',
                    isLoading: _isLoading,
                    onPressed: _login,
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
                      const Text('Belum Punya Akun? ', style: AppTextStyles.bodyText),
                      GestureDetector(
                        onTap: () => Navigator.pushNamed(context, AppRoutes.register),
                        child: const Text('Daftar Disini', style: AppTextStyles.linkText),
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
