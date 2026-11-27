import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../config/app_colors.dart';
import '../../config/app_text_styles.dart';
import '../../config/app_constants.dart';
import '../../widgets/home/stat_card_widget.dart';
import '../../widgets/home/recent_assesment_card.dart';
import '../../widgets/common/custom_button.dart';
import '../../data/services/dashboard_service.dart';
import '../../data/models/dashboard_model.dart';
import '../../data/models/assesment_model.dart';
import '../../app/auth_provider.dart';
import 'package:intl/intl.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _dashboardService = DashboardService();
  DashboardStatsModel? _stats;
  List<AssesmentModel>? _recent;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final stats = await _dashboardService.getStats();
      final recent = await _dashboardService.getRecent();
      if (mounted) {
        setState(() {
          _stats = stats;
          _recent = recent;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = 'Gagal memuat data dashboard.';
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final user = context.watch<AuthProvider>().user;
    final formatter = NumberFormat.decimalPattern('id');

    return SafeArea(
      child: RefreshIndicator(
        onRefresh: _loadData,
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(AppConstants.paddingNormal),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Selamat datang,', style: AppTextStyles.h2),
                        Text(
                          user?.namaLengkap ?? 'Guru',
                          style: AppTextStyles.h1.copyWith(color: AppColors.primary),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 4),
                        Text(
                          DateFormat('EEEE, dd MMMM yyyy', 'id_ID').format(DateTime.now()),
                          style: AppTextStyles.bodyText,
                        ),
                      ],
                    ),
                  ),
                  Row(
                    children: [
                      IconButton(
                        icon: const Icon(Icons.notifications_none, size: 28),
                        onPressed: () {},
                      ),
                      const SizedBox(width: 8),
                      const CircleAvatar(
                        backgroundColor: AppColors.slate300,
                        child: Icon(Icons.person, color: AppColors.white),
                      ),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: AppConstants.paddingLarge),

              if (_isLoading)
                const Center(child: Padding(
                  padding: EdgeInsets.all(32.0),
                  child: CircularProgressIndicator(),
                ))
              else if (_error != null)
                Center(
                  child: Column(
                    children: [
                      Text(_error!, style: TextStyle(color: AppColors.error)),
                      TextButton(onPressed: _loadData, child: const Text('Coba Lagi'))
                    ],
                  ),
                )
              else ...[
                // Statistics Grid
                Row(
                  children: [
                    Expanded(
                      child: StatCardWidget(
                        icon: Icons.bar_chart,
                        value: formatter.format(_stats?.totalSiswaDinilai ?? 0),
                        label: 'Siswa Yang Sudah Dinilai',
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: StatCardWidget(
                        icon: Icons.speed,
                        value: _stats?.rataRataNilai.toStringAsFixed(1) ?? '0.0',
                        label: 'Rata rata nilai siswa',
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: StatCardWidget(
                        icon: Icons.calendar_today,
                        value: formatter.format(_stats?.penilaianBulanIni ?? 0),
                        label: 'Penilaian Dibuat Bulan Ini',
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: StatCardWidget(
                        icon: Icons.emoji_events,
                        value: _stats?.nilaiTertinggi.toStringAsFixed(1) ?? '0.0',
                        label: 'Nilai Siswa Tertinggi',
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: AppConstants.paddingLarge),

                // Recent Assessments Header
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text('Penilaian Terbaru', style: AppTextStyles.h2),
                    TextButton(
                      onPressed: () {
                        // TODO: Navigate to Riwayat tab (index 1)
                      },
                      child: const Text('Lihat semua', style: AppTextStyles.linkText),
                    ),
                  ],
                ),
                const SizedBox(height: 8),

                // Table Header
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  decoration: const BoxDecoration(
                    color: AppColors.slate300,
                    borderRadius: BorderRadius.vertical(top: Radius.circular(8)),
                  ),
                  child: Row(
                    children: [
                      Expanded(flex: 2, child: Text('Nama Siswa', style: AppTextStyles.bodyText.copyWith(fontWeight: FontWeight.bold))),
                      Expanded(flex: 2, child: Text('Mata Pelajaran', style: AppTextStyles.bodyText.copyWith(fontWeight: FontWeight.bold))),
                      Expanded(flex: 1, child: Text('Nilai', style: AppTextStyles.bodyText.copyWith(fontWeight: FontWeight.bold))),
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
                  child: _recent == null || _recent!.isEmpty
                      ? const Padding(
                          padding: EdgeInsets.all(16.0),
                          child: Center(child: Text('Belum ada penilaian.')),
                        )
                      : Column(
                          children: _recent!.asMap().entries.map((entry) {
                            int idx = entry.key;
                            AssesmentModel assesment = entry.value;
                            return RecentAssesmentCard(
                              nama: assesment.namaSiswa,
                              mapel: assesment.mataPelajaran ?? '-',
                              nilai: assesment.isSelesai ? assesment.nilaiAkhir.toStringAsFixed(0) : '-',
                              status: assesment.status,
                              isFinished: assesment.isSelesai,
                              isEven: idx % 2 != 0,
                            );
                          }).toList(),
                        ),
                ),
                const SizedBox(height: AppConstants.paddingLarge),

                // Action Button
                CustomButton(
                  text: 'Mulai penilaian baru',
                  onPressed: () {
                    // TODO: Navigate to Penilaian tab
                  },
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
