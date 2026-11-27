import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import '../../config/app_text_styles.dart';
import '../../config/app_constants.dart';
import '../../config/app_colors.dart';
import '../../widgets/common/custom_button.dart';
import '../../widgets/penilaian/ocr_result_row.dart';
import '../../data/services/assesment_service.dart';

class PreviewOcrScreen extends StatefulWidget {
  const PreviewOcrScreen({super.key});

  @override
  State<PreviewOcrScreen> createState() => _PreviewOcrScreenState();
}

class _PreviewOcrScreenState extends State<PreviewOcrScreen> {
  final _assesmentService = AssesmentService();
  bool _isSaving = false;
  bool _isInit = true;

  List<Map<String, dynamic>> ocrResults = [];
  final List<Uint8List> _annotatedImagesBytes = [];
  late final PageController _pageController;
  int _currentImageIndex = 0;

  @override
  void initState() {
    super.initState();
    _pageController = PageController();
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_isInit) {
      final args = ModalRoute.of(context)?.settings.arguments as Map<String, dynamic>?;
      if (args != null && args.containsKey('prediction_result')) {
        final pred = args['prediction_result'] as Map<String, dynamic>;

        // Cek apakah ada evaluasi_ujian (sudah dicocokkan dengan kunci jawaban di backend)
        if (pred.containsKey('evaluasi_ujian') && pred['evaluasi_ujian'] != null) {
          final eval = pred['evaluasi_ujian'] as Map<String, dynamic>;
          final detail = eval['detail'] as List<dynamic>? ?? [];
          ocrResults = detail.map((e) {
            final map = e as Map<String, dynamic>;
            return {
              'no': map['nomor_soal'] ?? 0,
              'jwb': map['jawaban_siswa'] ?? '-',
              'kunci': map['kunci_jawaban'] ?? '-',
              'isBenar': map['is_benar'] == true,
            };
          }).toList();
        } else if (pred.containsKey('results')) {
          final results = pred['results'] as List<dynamic>? ?? [];
          ocrResults = results.map((e) {
            final map = e as Map<String, dynamic>;
            return {
              'no': map['nomor_soal'] ?? 0,
              'jwb': map['jawaban_terpilih'] ?? '-',
              'kunci': '-',
              'isBenar': false,
            };
          }).toList();
        }

        // Ambil gambar anotasi jika ada
        _annotatedImagesBytes.clear();
        
        if (pred.containsKey('annotated_images') && pred['annotated_images'] != null) {
          final imgList = pred['annotated_images'] as List<dynamic>;
          for (var imgStrDynamic in imgList) {
            final imgStr = imgStrDynamic as String;
            try {
              final commaIdx = imgStr.indexOf(',');
              final rawBase64 = commaIdx != -1 ? imgStr.substring(commaIdx + 1) : imgStr;
              _annotatedImagesBytes.add(base64Decode(rawBase64));
            } catch (_) {}
          }
        } else if (pred.containsKey('annotated_image') && pred['annotated_image'] != null) {
          // Fallback untuk backward compatibility
          final imgStr = pred['annotated_image'] as String;
          try {
            final commaIdx = imgStr.indexOf(',');
            final rawBase64 = commaIdx != -1 ? imgStr.substring(commaIdx + 1) : imgStr;
            _annotatedImagesBytes.add(base64Decode(rawBase64));
          } catch (_) {}
        }
      }
      _isInit = false;
    }
  }

  int get _totalBenar => ocrResults.where((e) => e['isBenar'] == true).length;
  int get _totalSalah => ocrResults.where((e) => e['isBenar'] == false).length;
  double get _nilaiAkhir {
    if (ocrResults.isEmpty) return 0.0;
    return (_totalBenar / ocrResults.length) * 100;
  }

  void _editJawaban(int index) {
    showDialog(
      context: context,
      builder: (context) {
        String newJwb = ocrResults[index]['jwb'];
        return AlertDialog(
          title: Text('Edit Jawaban No.${ocrResults[index]['no']}'),
          content: TextField(
            maxLength: 1,
            textCapitalization: TextCapitalization.characters,
            decoration: InputDecoration(
              labelText: 'Jawaban Siswa',
              hintText: ocrResults[index]['jwb'],
              border: const OutlineInputBorder(),
            ),
            onChanged: (val) => newJwb = val.toUpperCase().trim(),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Batal'),
            ),
            ElevatedButton(
              onPressed: () {
                setState(() {
                  ocrResults[index]['jwb'] = newJwb.isEmpty ? '-' : newJwb;
                  final kunci = ocrResults[index]['kunci'];
                  if (kunci != '-' && kunci != null) {
                    ocrResults[index]['isBenar'] = newJwb == kunci;
                  }
                });
                Navigator.pop(context);
              },
              child: const Text('Simpan'),
            )
          ],
        );
      },
    );
  }

  void _simpanHasil(Map<String, dynamic> args) async {
    setState(() => _isSaving = true);
    try {
      final detail = ocrResults.map((e) => {
        'nomor_soal': e['no'],
        'jawaban_siswa': e['jwb'],
      }).toList();

      await _assesmentService.createAssesment(
        ujianId: args['ujian_id'] as int,
        namaSiswa: args['nama_siswa'] as String,
        nisSiswa: args['nis_siswa'] as String,
        detail: detail,
      );

      if (mounted) {
        setState(() => _isSaving = false);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Berhasil menyimpan penilaian siswa'),
            backgroundColor: AppColors.success,
          ),
        );
        Navigator.pop(context); // kembali ke form
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isSaving = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Gagal menyimpan hasil penilaian: $e'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final args = ModalRoute.of(context)?.settings.arguments as Map<String, dynamic>?;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Preview Hasil Koreksi AI'),
      ),
      body: args == null
          ? const Center(child: Text('Data ujian tidak ditemukan'))
          : SingleChildScrollView(
              padding: const EdgeInsets.all(AppConstants.paddingLarge),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Info Siswa Header
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: AppColors.slate100,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: AppColors.border),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Siswa: ${args['nama_siswa'] ?? '-'}', style: AppTextStyles.h3),
                        const SizedBox(height: 4),
                        Text('NIS: ${args['nis_siswa'] ?? '-'}', style: AppTextStyles.bodyTextSmall),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Visualisasi Gambar Lembar Soal Beranotasi AI (Slider Horizontal / Carousel)
                  if (_annotatedImagesBytes.isNotEmpty) ...[
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        const Text('Hasil Deteksi Visual Lembar Soal (AI):', style: AppTextStyles.h3),
                        if (_annotatedImagesBytes.length > 1)
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(
                              color: AppColors.primary.withValues(alpha: 0.1),
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: AppColors.primary.withValues(alpha: 0.3)),
                            ),
                            child: Text(
                              'Lembar ${_currentImageIndex + 1} dari ${_annotatedImagesBytes.length}',
                              style: AppTextStyles.bodyTextSmall.copyWith(
                                color: AppColors.primary,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Container(
                      width: double.infinity,
                      height: 420,
                      decoration: BoxDecoration(
                        color: Colors.black.withValues(alpha: 0.04),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: AppColors.border),
                      ),
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(12),
                        child: Stack(
                          alignment: Alignment.center,
                          children: [
                            PageView.builder(
                              controller: _pageController,
                              physics: const BouncingScrollPhysics(),
                              itemCount: _annotatedImagesBytes.length,
                              onPageChanged: (idx) {
                                setState(() {
                                  _currentImageIndex = idx;
                                });
                              },
                              itemBuilder: (context, index) {
                                return InteractiveViewer(
                                  minScale: 1.0,
                                  maxScale: 4.0,
                                  child: Center(
                                    child: Image.memory(
                                      _annotatedImagesBytes[index],
                                      fit: BoxFit.contain,
                                    ),
                                  ),
                                );
                              },
                            ),
                            if (_annotatedImagesBytes.length > 1) ...[
                              // Tombol Navigasi Kiri (Previous)
                              Positioned(
                                left: 8,
                                child: Material(
                                  color: Colors.transparent,
                                  child: InkWell(
                                    onTap: _currentImageIndex > 0
                                        ? () {
                                            _pageController.previousPage(
                                              duration: const Duration(milliseconds: 300),
                                              curve: Curves.easeInOut,
                                            );
                                          }
                                        : null,
                                    borderRadius: BorderRadius.circular(20),
                                    child: Container(
                                      padding: const EdgeInsets.all(8),
                                      decoration: BoxDecoration(
                                        color: _currentImageIndex > 0
                                            ? Colors.black.withValues(alpha: 0.55)
                                            : Colors.black.withValues(alpha: 0.2),
                                        shape: BoxShape.circle,
                                      ),
                                      child: Icon(
                                        Icons.chevron_left,
                                        color: _currentImageIndex > 0 ? Colors.white : Colors.white38,
                                        size: 24,
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                              // Tombol Navigasi Kanan (Next)
                              Positioned(
                                right: 8,
                                child: Material(
                                  color: Colors.transparent,
                                  child: InkWell(
                                    onTap: _currentImageIndex < _annotatedImagesBytes.length - 1
                                        ? () {
                                            _pageController.nextPage(
                                              duration: const Duration(milliseconds: 300),
                                              curve: Curves.easeInOut,
                                            );
                                          }
                                        : null,
                                    borderRadius: BorderRadius.circular(20),
                                    child: Container(
                                      padding: const EdgeInsets.all(8),
                                      decoration: BoxDecoration(
                                        color: _currentImageIndex < _annotatedImagesBytes.length - 1
                                            ? Colors.black.withValues(alpha: 0.55)
                                            : Colors.black.withValues(alpha: 0.2),
                                        shape: BoxShape.circle,
                                      ),
                                      child: Icon(
                                        Icons.chevron_right,
                                        color: _currentImageIndex < _annotatedImagesBytes.length - 1
                                            ? Colors.white
                                            : Colors.white38,
                                        size: 24,
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                            ],
                            // Petunjuk zoom & swipe
                            Positioned(
                              bottom: 8,
                              right: 12,
                              child: Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                decoration: BoxDecoration(
                                  color: Colors.black.withValues(alpha: 0.45),
                                  borderRadius: BorderRadius.circular(6),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    const Icon(Icons.zoom_in, color: Colors.white70, size: 14),
                                    const SizedBox(width: 4),
                                    Text(
                                      _annotatedImagesBytes.length > 1
                                          ? 'Geser / Zoom gambar'
                                          : 'Cubit untuk zoom',
                                      style: const TextStyle(color: Colors.white, fontSize: 11),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    if (_annotatedImagesBytes.length > 1) ...[
                      const SizedBox(height: 10),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: List.generate(
                          _annotatedImagesBytes.length,
                          (idx) => GestureDetector(
                            onTap: () {
                              _pageController.animateToPage(
                                idx,
                                duration: const Duration(milliseconds: 300),
                                curve: Curves.easeInOut,
                              );
                            },
                            child: AnimatedContainer(
                              duration: const Duration(milliseconds: 250),
                              margin: const EdgeInsets.symmetric(horizontal: 4),
                              width: _currentImageIndex == idx ? 22 : 8,
                              height: 8,
                              decoration: BoxDecoration(
                                color: _currentImageIndex == idx
                                    ? AppColors.primary
                                    : AppColors.slate300,
                                borderRadius: BorderRadius.circular(4),
                              ),
                            ),
                          ),
                        ),
                      ),
                    ],
                    const SizedBox(height: 16),
                  ],

                  const Text('STEP 3 — Hasil Koreksi Otomatis', style: AppTextStyles.h2),
                  const SizedBox(height: 4),
                  const Text('Ketuk baris untuk mengoreksi jawaban jika deteksi kurang tepat', style: AppTextStyles.bodyTextSmall),
                  const SizedBox(height: AppConstants.paddingNormal),

                  if (ocrResults.isEmpty)
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(24),
                      decoration: BoxDecoration(
                        color: AppColors.slate100,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: AppColors.border),
                      ),
                      child: const Center(
                        child: Text(
                          'Tidak ada soal yang terdeteksi pada gambar.\nSilakan coba foto ulang dengan pencahayaan yang lebih baik.',
                          textAlign: TextAlign.center,
                          style: AppTextStyles.bodyText,
                        ),
                      ),
                    )
                  else ...[
                    // Table Header
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      decoration: const BoxDecoration(
                        color: AppColors.slate300,
                        borderRadius: BorderRadius.vertical(top: Radius.circular(8)),
                      ),
                      child: Row(
                        children: [
                          Expanded(flex: 1, child: Text('No', style: AppTextStyles.bodyText.copyWith(fontWeight: FontWeight.bold))),
                          Expanded(flex: 2, child: Text('Jwb Siswa', style: AppTextStyles.bodyText.copyWith(fontWeight: FontWeight.bold))),
                          Expanded(flex: 2, child: Text('Kunci Jwb', style: AppTextStyles.bodyText.copyWith(fontWeight: FontWeight.bold))),
                          Expanded(flex: 2, child: Text('Status', style: AppTextStyles.bodyText.copyWith(fontWeight: FontWeight.bold))),
                        ],
                      ),
                    ),

                    // Table Body
                    Container(
                      decoration: BoxDecoration(
                        border: Border.all(color: AppColors.slate300),
                        borderRadius: const BorderRadius.vertical(bottom: Radius.circular(8)),
                      ),
                      child: Column(
                        children: ocrResults.asMap().entries.map((entry) {
                          int idx = entry.key;
                          var data = entry.value;
                          return OcrResultRow(
                            no: data['no'],
                            jwbSiswa: data['jwb'],
                            kunciJwb: data['kunci'],
                            isBenar: data['isBenar'],
                            isEven: idx % 2 != 0,
                            onTap: () => _editJawaban(idx),
                          );
                        }).toList(),
                      ),
                    ),
                    const SizedBox(height: 30),

                    // Summary
                    const Text('Ringkasan Hasil Koreksi:', style: AppTextStyles.h3),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                          child: Container(
                            padding: const EdgeInsets.all(16),
                            decoration: BoxDecoration(
                              color: AppColors.success.withValues(alpha: 0.1),
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: AppColors.success),
                            ),
                            child: Column(
                              children: [
                                const Text('Benar', style: AppTextStyles.bodyText),
                                Text('$_totalBenar', style: AppTextStyles.h2.copyWith(color: AppColors.success)),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Container(
                            padding: const EdgeInsets.all(16),
                            decoration: BoxDecoration(
                              color: AppColors.error.withValues(alpha: 0.1),
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: AppColors.error),
                            ),
                            child: Column(
                              children: [
                                const Text('Salah', style: AppTextStyles.bodyText),
                                Text('$_totalSalah', style: AppTextStyles.h2.copyWith(color: AppColors.error)),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: AppColors.primary.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: AppColors.primary),
                      ),
                      child: Column(
                        children: [
                          const Text('Nilai Akhir', style: AppTextStyles.bodyText),
                          Text(_nilaiAkhir.toStringAsFixed(2), style: AppTextStyles.h1.copyWith(color: AppColors.primary)),
                        ],
                      ),
                    ),
                  ],

                  const SizedBox(height: 40),
                  CustomButton(
                    text: 'SIMPAN HASIL PENILAIAN',
                    isLoading: _isSaving,
                    onPressed: ocrResults.isEmpty ? null : () => _simpanHasil(args),
                  ),
                  const SizedBox(height: 16),
                  CustomButton(
                    text: 'BATAL',
                    isOutlined: true,
                    onPressed: () => Navigator.pop(context),
                  ),
                  const SizedBox(height: 20),
                ],
              ),
            ),
    );
  }
}

