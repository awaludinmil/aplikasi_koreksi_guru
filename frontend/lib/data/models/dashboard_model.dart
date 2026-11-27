class DashboardStatsModel {
  final int totalSiswaDinilai;
  final double rataRataNilai;
  final double nilaiTertinggi;
  final int penilaianBulanIni;

  DashboardStatsModel({
    required this.totalSiswaDinilai,
    required this.rataRataNilai,
    required this.nilaiTertinggi,
    required this.penilaianBulanIni,
  });

  factory DashboardStatsModel.fromJson(Map<String, dynamic> json) {
    return DashboardStatsModel(
      totalSiswaDinilai: json['total_siswa_dinilai'] as int,
      rataRataNilai: (json['rata_rata_nilai'] as num).toDouble(),
      nilaiTertinggi: (json['nilai_tertinggi'] as num).toDouble(),
      penilaianBulanIni: json['penilaian_bulan_ini'] as int,
    );
  }
}
