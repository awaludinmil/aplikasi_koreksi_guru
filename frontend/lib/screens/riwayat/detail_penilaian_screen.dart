import 'package:flutter/material.dart';
import '../../config/app_text_styles.dart';
import '../../config/app_constants.dart';
import '../../config/app_colors.dart';
import '../../widgets/penilaian/ocr_result_row.dart';
import '../../app/routes.dart';
import '../../data/services/assesment_service.dart';
import '../../data/services/ujian_service.dart';
import '../../data/models/assesment_model.dart';
import '../../data/models/ujian_model.dart';

class DetailPenilaianScreen extends StatefulWidget {
  const DetailPenilaianScreen({super.key});

  @override
  State<DetailPenilaianScreen> createState() => _DetailPenilaianScreenState();
}

class _DetailPenilaianScreenState extends State<DetailPenilaianScreen> {
  final _assesmentService = AssesmentService();
  final _ujianService = UjianService();
  
  bool _isLoading = true;
  String? _errorMessage;
  
  AssesmentModel? _assesment;
  UjianModel? _ujian;
  
  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_assesment == null && _isLoading) {
      final args = ModalRoute.of(context)?.settings.arguments;
      if (args is int) {
        _loadData(args);
      } else {
        setState(() {
          _isLoading = false;
          _errorMessage = 'ID Penilaian tidak valid';
        });
      }
    }
  }

  Future<void> _loadData(int assesmentId) async {
    try {
      final assesment = await _assesmentService.getDetail(assesmentId);
      final ujian = await _ujianService.getUjianDetail(assesment.ujianId);
      
      if (mounted) {
        setState(() {
          _assesment = assesment;
          _ujian = ujian;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = 'Gagal memuat data: ${e.toString()}';
          _isLoading = false;
        });
      }
    }
  }

  String _getKunciJawaban(int nomorSoal) {
    if (_ujian == null) return '-';
    final kunciList = _ujian!.kunciJawaban.where((k) => k.nomorSoal == nomorSoal).toList();
    if (kunciList.isNotEmpty) {
      return kunciList.first.kunci;
    }
    return '-';
  }

  String _getPredikat(double nilai) {
    if (nilai >= 85) return 'A (Sangat Baik)';
    if (nilai >= 70) return 'B (Baik)';
    if (nilai >= 55) return 'C (Cukup)';
    if (nilai >= 40) return 'D (Kurang)';
    return 'E (Sangat Kurang)';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Detail Koreksi'),
        actions: [
          if (_assesment != null)
            IconButton(
              icon: const Icon(Icons.edit),
              onPressed: () => Navigator.pushNamed(
                context, 
                AppRoutes.editPenilaian,
                arguments: _assesment!.assesmentId,
              ),
            ),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    
    if (_errorMessage != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48, color: AppColors.error),
            const SizedBox(height: 16),
            Text(_errorMessage!, style: AppTextStyles.bodyText, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () {
                final args = ModalRoute.of(context)?.settings.arguments;
                if (args is int) {
                  setState(() { _isLoading = true; _errorMessage = null; });
                  _loadData(args);
                }
              },
              child: const Text('Coba Lagi'),
            )
          ],
        ),
      );
    }
    
    if (_assesment == null) {
      return const Center(child: Text('Data tidak ditemukan'));
    }

    final double nilai = _assesment!.nilaiAkhir;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(AppConstants.paddingLarge),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(16),
            width: double.infinity,
            decoration: BoxDecoration(
              color: AppColors.slate100,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('=== DATA SISWA ===', style: AppTextStyles.h3),
                const SizedBox(height: 8),
                Text('Nama Siswa: ${_assesment!.namaSiswa}', style: AppTextStyles.bodyText),
                Text('NIS: ${_assesment!.nisSiswa}', style: AppTextStyles.bodyText),
                const SizedBox(height: 16),
                const Text('=== DATA UJIAN ===', style: AppTextStyles.h3),
                const SizedBox(height: 8),
                Text('Ujian: ${_ujian?.mataPelajaran ?? _assesment!.mataPelajaran ?? '-'} - ${_ujian?.kelas ?? _assesment!.kelas ?? '-'}', style: AppTextStyles.bodyText),
                Text('Tanggal Ujian: ${_ujian?.tanggalUjian ?? _assesment!.tanggalUjian ?? '-'}', style: AppTextStyles.bodyText),
              ],
            ),
          ),
          const SizedBox(height: 24),
          
          const Text('Hasil Akhir', style: AppTextStyles.h2),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(16),
            width: double.infinity,
            decoration: BoxDecoration(
              border: Border.all(color: AppColors.primary),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Column(
              children: [
                Text('${nilai.toStringAsFixed(2)} / 100', style: AppTextStyles.h1.copyWith(color: AppColors.primary)),
                const SizedBox(height: 8),
                LinearProgressIndicator(value: nilai / 100, backgroundColor: AppColors.slate300),
                const SizedBox(height: 8),
                Text('Predikat: ${_getPredikat(nilai)}', style: AppTextStyles.bodyText),
                const SizedBox(height: 8),
                Text('Benar: ${_assesment!.totalBenar} | Salah: ${_assesment!.totalSalah}', style: AppTextStyles.bodyTextSmall),
              ],
            ),
          ),
          const SizedBox(height: 24),
          
          const Text('Koreksi Per Soal', style: AppTextStyles.h2),
          const SizedBox(height: 16),
          
          if (_assesment!.detail.isEmpty)
            const Center(child: Text('Tidak ada data detail jawaban.'))
          else
            Container(
              decoration: BoxDecoration(
                border: Border.all(color: AppColors.border),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                children: _assesment!.detail.asMap().entries.map((entry) {
                  final index = entry.key;
                  final d = entry.value;
                  return OcrResultRow(
                    no: d.nomorSoal,
                    jwbSiswa: d.jawabanSiswa,
                    kunciJwb: _getKunciJawaban(d.nomorSoal),
                    isBenar: d.isBenar,
                    isEven: index % 2 != 0,
                    onTap: () {},
                  );
                }).toList(),
              ),
            ),
        ],
      ),
    );
  }
}
