import '../models/dashboard_model.dart';
import '../models/assesment_model.dart';
import 'api_client.dart';

class DashboardService {
  /// Ambil statistik rekap penilaian guru yang login.
  Future<DashboardStatsModel> getStats() async {
    final data = await ApiClient.get('/dashboard/stats');
    return DashboardStatsModel.fromJson(data);
  }

  /// Ambil 5 penilaian terbaru dari guru yang login.
  Future<List<AssesmentModel>> getRecent() async {
    final data = await ApiClient.get('/dashboard/recent');
    final list = data['recent'] as List<dynamic>;
    return list
        .map((e) => AssesmentModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }
}
