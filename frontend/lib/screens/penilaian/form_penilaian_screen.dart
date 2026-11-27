import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../../config/app_text_styles.dart';
import '../../config/app_constants.dart';
import '../../config/app_colors.dart';
import '../../widgets/common/custom_text_field.dart';
import '../../widgets/common/custom_button.dart';
import '../../widgets/penilaian/camera_placeholder_widget.dart';
import '../../app/routes.dart';
import '../../data/models/ujian_model.dart';
import '../../data/services/ujian_service.dart';
import '../../data/services/assesment_service.dart';

class FormPenilaianScreen extends StatefulWidget {
  const FormPenilaianScreen({super.key});

  @override
  State<FormPenilaianScreen> createState() => _FormPenilaianScreenState();
}

class _FormPenilaianScreenState extends State<FormPenilaianScreen> {
  final _formKey = GlobalKey<FormState>();
  final _namaController = TextEditingController();
  final _nisController = TextEditingController();
  
  final UjianService _ujianService = UjianService();
  final AssesmentService _assesmentService = AssesmentService();
  final ImagePicker _picker = ImagePicker();

  final _scrollController = ScrollController();

  List<UjianModel> _ujianList = [];
  int? _selectedUjianId;
  bool _isLoading = true;
  bool _isProcessingOcr = false;

  // Selected image state
  List<Map<String, dynamic>> _imagesList = [];

  @override
  void initState() {
    super.initState();
    _loadUjian();
  }

  @override
  void dispose() {
    _namaController.dispose();
    _nisController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _loadUjian() async {
    try {
      final data = await _ujianService.getUjianList();
      if (mounted) {
        setState(() {
          _ujianList = data;
          if (_ujianList.isNotEmpty && _selectedUjianId == null) {
            _selectedUjianId = _ujianList.first.ujianId;
          }
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Gagal memuat daftar ujian')),
        );
      }
    }
  }

  Future<void> _pickImage(ImageSource source) async {
    try {
      if (source == ImageSource.gallery) {
        final List<XFile> pickedFiles = await _picker.pickMultiImage(
          maxWidth: 2048,
          maxHeight: 2048,
          imageQuality: 90,
        );
        
        if (pickedFiles.isNotEmpty) {
          int added = 0;
          for (var picked in pickedFiles) {
            if (_imagesList.length >= 4) break;
            final bytes = await picked.readAsBytes();
            setState(() {
              _imagesList.add({'bytes': bytes, 'filename': picked.name});
            });
            added++;
          }
          
          if (added < pickedFiles.length && mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Maksimal 4 gambar yang dapat dipilih')),
            );
          }
        }
      } else {
        final XFile? picked = await _picker.pickImage(
          source: source,
          maxWidth: 2048,
          maxHeight: 2048,
          imageQuality: 90,
        );

        if (picked != null) {
          if (_imagesList.length < 4) {
            final bytes = await picked.readAsBytes();
            setState(() {
              _imagesList.add({'bytes': bytes, 'filename': picked.name});
            });
          } else if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Maksimal 4 gambar yang dapat dipilih')),
            );
          }
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Gagal memilih gambar: $e')),
        );
      }
    }
  }

  void _removeImage(int index) {
    setState(() {
      _imagesList.removeAt(index);
    });
  }

  Future<void> _processOcr() async {
    if (!_formKey.currentState!.validate()) {
      _scrollController.animateTo(
        0,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Mohon lengkapi data ujian, nama siswa, dan NIS terlebih dahulu.'),
          backgroundColor: AppColors.error,
        ),
      );
      return;
    }

    if (_selectedUjianId == null) {
      _scrollController.animateTo(
        0,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Silakan pilih Master Ujian terlebih dahulu di Step 1.'),
          backgroundColor: AppColors.error,
        ),
      );
      return;
    }

    if (_imagesList.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Silakan ambil foto atau pilih foto lembar jawaban dari galeri terlebih dahulu.'),
          backgroundColor: AppColors.error,
        ),
      );
      return;
    }

    setState(() => _isProcessingOcr = true);

    try {
      // Panggil backend API /api/assesment/predict
      final result = await _assesmentService.predictLembarSoal(
        imageDataList: _imagesList,
        ujianId: _selectedUjianId!,
        threshold: 0.40,
      );

      if (mounted) {
        setState(() => _isProcessingOcr = false);

        // Arahkan ke screen Preview OCR dengan membawa data hasil evaluasi asli dari backend
        Navigator.pushNamed(
          context,
          AppRoutes.previewOcr,
          arguments: {
            'ujian_id': _selectedUjianId,
            'nama_siswa': _namaController.text,
            'nis_siswa': _nisController.text,
            'prediction_result': result,
          },
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isProcessingOcr = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Gagal memproses AI & OCR: $e'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Koreksi Jawaban'),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              controller: _scrollController,
              padding: const EdgeInsets.all(AppConstants.paddingLarge),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('STEP 1 — Pilih Master Ujian', style: AppTextStyles.h2),
                    const SizedBox(height: AppConstants.paddingNormal),
                    DropdownButtonFormField<int>(
                      decoration: const InputDecoration(
                        labelText: 'Pilih Ujian',
                        border: OutlineInputBorder(),
                      ),
                      value: _selectedUjianId,
                      items: _ujianList.map((ujian) {
                        return DropdownMenuItem<int>(
                          value: ujian.ujianId,
                          child: Text(ujian.label),
                        );
                      }).toList(),
                      onChanged: (val) {
                        setState(() {
                          _selectedUjianId = val;
                        });
                      },
                      validator: (val) => val == null ? 'Wajib dipilih' : null,
                    ),
                    const SizedBox(height: 30),
                    const Divider(color: AppColors.border),
                    const SizedBox(height: 30),
                    const Text('STEP 2 — Isi Data Siswa', style: AppTextStyles.h2),
                    const SizedBox(height: AppConstants.paddingNormal),
                    CustomTextField(
                      label: 'Nama Siswa',
                      controller: _namaController,
                      validator: (val) => val == null || val.isEmpty ? 'Wajib diisi' : null,
                    ),
                    const SizedBox(height: 12),
                    CustomTextField(
                      label: 'NIS (Nomor Induk Siswa)',
                      controller: _nisController,
                      keyboardType: TextInputType.number,
                      validator: (val) => val == null || val.isEmpty ? 'Wajib diisi' : null,
                    ),
                    const SizedBox(height: 30),
                    const Divider(color: AppColors.border),
                    const SizedBox(height: 30),
                    const Text('STEP 3 — Upload Lembar Jawaban', style: AppTextStyles.h2),
                    const SizedBox(height: AppConstants.paddingNormal),
                    CameraPlaceholderWidget(
                      images: _imagesList,
                      onCameraTap: () => _pickImage(ImageSource.camera),
                      onGalleryTap: () => _pickImage(ImageSource.gallery),
                      onRemoveTap: _removeImage,
                    ),
                    const SizedBox(height: 24),
                    CustomButton(
                      text: _isProcessingOcr
                          ? 'MEMPROSES KOREKSI AI...'
                          : 'PROSES KOREKSI LEMBAR JAWABAN',
                      isLoading: _isProcessingOcr,
                      onPressed: _isProcessingOcr ? null : () => _processOcr(),
                    ),
                    const SizedBox(height: 40),
                  ],
                ),
              ),
            ),
    );
  }
}
