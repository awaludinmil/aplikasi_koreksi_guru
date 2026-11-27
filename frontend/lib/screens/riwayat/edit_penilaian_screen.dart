import 'package:flutter/material.dart';
import '../../config/app_colors.dart';
import '../../config/app_constants.dart';
import '../../config/app_text_styles.dart';
import '../../widgets/common/custom_text_field.dart';
import '../../widgets/common/custom_button.dart';

class EditPenilaianScreen extends StatefulWidget {
  const EditPenilaianScreen({super.key});

  @override
  State<EditPenilaianScreen> createState() => _EditPenilaianScreenState();
}

class _EditPenilaianScreenState extends State<EditPenilaianScreen> {
  final _formKey = GlobalKey<FormState>();
  final _namaController = TextEditingController(text: 'Budi Santoso');
  final _nisController = TextEditingController(text: '2024001');

  final List<String> _kunciMaster = ['A', 'C', 'B', 'D'];
  final List<String> _jawabanSiswa = ['A', 'A', 'B', 'D'];

  void _simpanPerubahan() {
    if (_formKey.currentState!.validate()) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Perubahan berhasil disimpan')),
      );
      Navigator.pop(context);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Edit Data Penilaian'),
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(AppConstants.paddingLarge),
          children: [
            const Text('Data Siswa', style: AppTextStyles.h2),
            const SizedBox(height: 16),
            CustomTextField(
              label: 'Nama Siswa',
              controller: _namaController,
              validator: (val) => val == null || val.isEmpty ? 'Wajib diisi' : null,
            ),
            const SizedBox(height: 12),
            CustomTextField(
              label: 'NIS',
              controller: _nisController,
              validator: (val) => val == null || val.isEmpty ? 'Wajib diisi' : null,
            ),
            
            const SizedBox(height: 24),
            const Divider(color: AppColors.border),
            const SizedBox(height: 16),
            
            const Text('Koreksi Jawaban Manual', style: AppTextStyles.h2),
            const SizedBox(height: 16),
            
            Container(
              decoration: BoxDecoration(
                border: Border.all(color: AppColors.border),
                borderRadius: BorderRadius.circular(8),
              ),
              child: ListView.separated(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: _kunciMaster.length,
                separatorBuilder: (context, index) => const Divider(height: 1),
                itemBuilder: (context, index) {
                  final isBenar = _kunciMaster[index] == _jawabanSiswa[index];
                  return ListTile(
                    leading: Text('${index + 1}', style: AppTextStyles.h3),
                    title: Row(
                      children: [
                        Text('Siswa: ', style: AppTextStyles.bodyTextSmall),
                        DropdownButton<String>(
                          value: _jawabanSiswa[index],
                          items: ['A', 'B', 'C', 'D', 'E', '-'].map((val) => DropdownMenuItem(
                            value: val,
                            child: Text(val),
                          )).toList(),
                          onChanged: (val) {
                            setState(() {
                              _jawabanSiswa[index] = val!;
                            });
                          },
                        ),
                      ],
                    ),
                    subtitle: Text('Kunci: ${_kunciMaster[index]}', style: AppTextStyles.bodyTextSmall),
                    trailing: isBenar
                        ? const Icon(Icons.check_circle, color: AppColors.success)
                        : const Icon(Icons.cancel, color: AppColors.error),
                  );
                },
              ),
            ),
            
            const SizedBox(height: 32),
            CustomButton(
              text: 'SIMPAN PERUBAHAN',
              onPressed: _simpanPerubahan,
            ),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }
}
