import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../config/app_colors.dart';
import '../../config/app_constants.dart';
import '../../config/app_text_styles.dart';
import '../../widgets/common/custom_text_field.dart';
import '../../widgets/common/custom_button.dart';
import '../../data/models/ujian_model.dart';
import '../../data/services/ujian_service.dart';

class UjianFormScreen extends StatefulWidget {
  final UjianModel? ujian;

  const UjianFormScreen({super.key, this.ujian});

  @override
  State<UjianFormScreen> createState() => _UjianFormScreenState();
}

class _UjianFormScreenState extends State<UjianFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _ujianService = UjianService();
  
  final _kelasController = TextEditingController();
  final _mapelController = TextEditingController();
  final _tahunController = TextEditingController();
  final _tanggalController = TextEditingController();
  
  List<String> _kunciJawaban = [];
  bool _isSaving = false;

  @override
  void initState() {
    super.initState();
    if (widget.ujian != null) {
      _kelasController.text = widget.ujian!.kelas;
      _mapelController.text = widget.ujian!.mataPelajaran;
      _tahunController.text = widget.ujian!.tahunAjaran;
      _tanggalController.text = widget.ujian!.tanggalUjian;
      _kunciJawaban = widget.ujian!.kunciJawaban.map((k) => k.kunci).toList();
    }
  }

  void _addSoal() {
    setState(() {
      _kunciJawaban.add('A');
    });
  }

  void _removeSoal(int index) {
    setState(() {
      _kunciJawaban.removeAt(index);
    });
  }
  
  Future<void> _pilihTanggal() async {
    final DateTime? picked = await showDatePicker(
      context: context,
      initialDate: DateTime.now(),
      firstDate: DateTime(2000),
      lastDate: DateTime(2100),
    );
    if (picked != null) {
      setState(() {
        _tanggalController.text = DateFormat('yyyy-MM-dd').format(picked);
      });
    }
  }

  Future<void> _simpanUjian() async {
    if (!_formKey.currentState!.validate()) return;
    if (_kunciJawaban.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Tambahkan minimal 1 soal kunci jawaban')),
      );
      return;
    }
    
    setState(() => _isSaving = true);
    try {
      final kunciList = _kunciJawaban.asMap().entries.map((e) {
        return {
          'nomor_soal': e.key + 1,
          'kunci': e.value,
        };
      }).toList();

      if (widget.ujian == null) {
        // Create
        await _ujianService.createUjian(
          kelas: _kelasController.text.trim(),
          mataPelajaran: _mapelController.text.trim(),
          tahunAjaran: _tahunController.text.trim(),
          tanggalUjian: _tanggalController.text.trim(),
          kunciJawaban: kunciList,
        );
      } else {
        // Update
        await _ujianService.updateUjian(
          widget.ujian!.ujianId,
          kelas: _kelasController.text.trim(),
          mataPelajaran: _mapelController.text.trim(),
          tahunAjaran: _tahunController.text.trim(),
          tanggalUjian: _tanggalController.text.trim(),
          kunciJawaban: kunciList,
        );
      }

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Master Ujian Berhasil Disimpan')),
        );
        Navigator.pop(context, true); // true indicates success/refresh
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Gagal menyimpan: $e')),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isSaving = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isEdit = widget.ujian != null;
    return Scaffold(
      appBar: AppBar(
        title: Text(isEdit ? 'Edit Master Ujian' : 'Buat Master Ujian'),
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(AppConstants.paddingLarge),
          children: [
            CustomTextField(
              label: 'Mata Pelajaran',
              controller: _mapelController,
              validator: (val) => val == null || val.isEmpty ? 'Wajib diisi' : null,
            ),
            const SizedBox(height: 12),
            CustomTextField(
              label: 'Kelas',
              controller: _kelasController,
              validator: (val) => val == null || val.isEmpty ? 'Wajib diisi' : null,
            ),
            const SizedBox(height: 12),
            CustomTextField(
              label: 'Tahun Ajaran',
              controller: _tahunController,
              validator: (val) => val == null || val.isEmpty ? 'Wajib diisi' : null,
            ),
            const SizedBox(height: 12),
            GestureDetector(
              onTap: _pilihTanggal,
              child: AbsorbPointer(
                child: CustomTextField(
                  label: 'Tanggal Ujian (YYYY-MM-DD)',
                  controller: _tanggalController,
                  validator: (val) => val == null || val.isEmpty ? 'Wajib diisi' : null,
                ),
              ),
            ),
            const SizedBox(height: 24),
            const Divider(color: AppColors.border),
            const SizedBox(height: 16),
            
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Kunci Jawaban', style: AppTextStyles.h2),
                TextButton.icon(
                  onPressed: _addSoal,
                  icon: const Icon(Icons.add, color: AppColors.primary),
                  label: Text('Tambah Soal', style: AppTextStyles.buttonText.copyWith(color: AppColors.primary)),
                ),
              ],
            ),
            const SizedBox(height: 16),
            
            if (_kunciJawaban.isEmpty)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 32),
                child: Center(child: Text('Belum ada soal ditambahkan', style: AppTextStyles.bodyTextSmall)),
              ),
              
            ...List.generate(_kunciJawaban.length, (index) {
              return Padding(
                padding: const EdgeInsets.only(bottom: 8.0),
                child: Row(
                  children: [
                    SizedBox(
                      width: 50,
                      child: Text('No ${index + 1}.', style: AppTextStyles.h3),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: DropdownButtonFormField<String>(
                        value: _kunciJawaban[index],
                        decoration: const InputDecoration(
                          border: OutlineInputBorder(),
                          contentPadding: EdgeInsets.symmetric(horizontal: 16),
                        ),
                        items: ['A', 'B', 'C', 'D', 'E'].map((String value) {
                          return DropdownMenuItem<String>(
                            value: value,
                            child: Text(value),
                          );
                        }).toList(),
                        onChanged: (newValue) {
                          if (newValue != null) {
                            setState(() {
                              _kunciJawaban[index] = newValue;
                            });
                          }
                        },
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.remove_circle_outline, color: AppColors.error),
                      onPressed: () => _removeSoal(index),
                    )
                  ],
                ),
              );
            }),
            
            const SizedBox(height: 32),
            _isSaving
                ? const Center(child: CircularProgressIndicator())
                : CustomButton(
                    text: isEdit ? 'SIMPAN PERUBAHAN' : 'SIMPAN MASTER UJIAN',
                    onPressed: _simpanUjian,
                  ),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }
}
