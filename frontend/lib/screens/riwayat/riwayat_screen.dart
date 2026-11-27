import 'package:flutter/material.dart';
import '../../config/app_text_styles.dart';
import '../../config/app_constants.dart';
import '../../config/app_colors.dart';
import '../../app/routes.dart';
import '../../data/services/assesment_service.dart';
import '../../data/models/assesment_model.dart';
import 'dart:async';

class RiwayatScreen extends StatefulWidget {
  const RiwayatScreen({super.key});

  @override
  State<RiwayatScreen> createState() => _RiwayatScreenState();
}

class _RiwayatScreenState extends State<RiwayatScreen> {
  final _assesmentService = AssesmentService();
  bool _isLoading = true;
  List<AssesmentModel> _assesments = [];
  int _total = 0;
  
  String _searchQuery = '';
  Timer? _debounce;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  @override
  void dispose() {
    _debounce?.cancel();
    super.dispose();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    try {
      final data = await _assesmentService.getRiwayat(q: _searchQuery);
      if (mounted) {
        setState(() {
          _assesments = data['assesment'];
          _total = data['total'];
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Gagal memuat riwayat penilaian')),
        );
      }
    }
  }

  void _onSearchChanged(String query) {
    if (_debounce?.isActive ?? false) _debounce!.cancel();
    _debounce = Timer(const Duration(milliseconds: 500), () {
      _searchQuery = query;
      _loadData();
    });
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: RefreshIndicator(
        onRefresh: _loadData,
        child: Padding(
          padding: const EdgeInsets.all(AppConstants.paddingLarge),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Riwayat Penilaian Siswa', style: AppTextStyles.h1),
              const SizedBox(height: 8),
              const Text('Semua data di bawah adalah siswa yang sudah dinilai.', style: AppTextStyles.bodyTextSmall),
              const SizedBox(height: 24),
              
              // Search Bar
              TextField(
                onChanged: _onSearchChanged,
                decoration: InputDecoration(
                  hintText: 'Cari nama siswa / NIS...',
                  prefixIcon: const Icon(Icons.search),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                ),
              ),
              const SizedBox(height: 16),
              
              // Filters (Dummy for now, can implement later)
              Row(
                children: [
                  const Text('Filter: ', style: AppTextStyles.bodyText),
                  const SizedBox(width: 8),
                  DropdownButton<String>(
                    value: 'Semua',
                    items: ['Semua'].map((e) => DropdownMenuItem(value: e, child: Text(e))).toList(),
                    onChanged: (val) {},
                  ),
                ],
              ),
              const SizedBox(height: 24),
              
              Text('Total: $_total Siswa', style: AppTextStyles.h3),
              const SizedBox(height: 12),
              
              // List
              Expanded(
                child: _isLoading
                    ? const Center(child: CircularProgressIndicator())
                    : _assesments.isEmpty
                        ? const Center(child: Text('Tidak ada data penilaian.'))
                        : ListView.separated(
                            physics: const AlwaysScrollableScrollPhysics(),
                            itemCount: _assesments.length,
                            separatorBuilder: (context, index) => const SizedBox(height: 12),
                            itemBuilder: (context, index) {
                              return _buildHistoryCard(_assesments[index]);
                            },
                          ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHistoryCard(AssesmentModel assesment) {
    return InkWell(
      onTap: () => Navigator.pushNamed(
        context, 
        AppRoutes.detailPenilaian,
        arguments: assesment.assesmentId,
      ),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          border: Border.all(color: AppColors.border),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(assesment.namaSiswa, style: AppTextStyles.h3),
                IconButton(
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                  icon: const Icon(Icons.edit, size: 20, color: AppColors.primary),
                  onPressed: () => Navigator.pushNamed(
                    context, 
                    AppRoutes.editPenilaian,
                    arguments: assesment.assesmentId,
                  ),
                ),
              ],
            ),
            Text('NIS: ${assesment.nisSiswa}', style: AppTextStyles.bodyTextSmall),
            const Divider(),
            Text('Ujian: ${assesment.mataPelajaran ?? '-'} - ${assesment.kelas ?? '-'}', style: AppTextStyles.bodyText),
            Text('Status: ${assesment.status}', style: AppTextStyles.bodyTextSmall),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Nilai: ${assesment.isSelesai ? assesment.nilaiAkhir.toStringAsFixed(1) : '-'}', 
                  style: AppTextStyles.h2.copyWith(color: AppColors.primary)
                ),
                Text('Benar: ${assesment.totalBenar} | Salah: ${assesment.totalSalah}', style: AppTextStyles.bodyText),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
