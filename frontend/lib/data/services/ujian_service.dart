import '../models/ujian_model.dart';
import 'api_client.dart';

class UjianService {
  /// Ambil semua ujian milik guru yang login.
  Future<List<UjianModel>> getUjianList() async {
    final data = await ApiClient.get('/ujian/');
    final list = data['ujian'] as List<dynamic>;
    return list
        .map((e) => UjianModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// Ambil detail satu ujian beserta kunci jawaban.
  Future<UjianModel> getUjianDetail(int ujianId) async {
    final data = await ApiClient.get('/ujian/$ujianId');
    return UjianModel.fromJson(data['ujian'] as Map<String, dynamic>);
  }

  /// Buat ujian baru beserta kunci jawaban.
  /// [kunciJawaban] : list of { 'nomor_soal': int, 'kunci': 'A'|'B'|'C'|'D' }
  Future<UjianModel> createUjian({
    required String kelas,
    required String mataPelajaran,
    required String tahunAjaran,
    required String tanggalUjian, // format: YYYY-MM-DD
    required List<Map<String, dynamic>> kunciJawaban,
  }) async {
    final data = await ApiClient.post('/ujian/', {
      'kelas': kelas,
      'mata_pelajaran': mataPelajaran,
      'tahun_ajaran': tahunAjaran,
      'tanggal_ujian': tanggalUjian,
      'kunci_jawaban': kunciJawaban,
    });
    return UjianModel.fromJson(data['ujian'] as Map<String, dynamic>);
  }

  /// Edit ujian dan/atau kunci jawaban.
  Future<UjianModel> updateUjian(
    int ujianId, {
    String? kelas,
    String? mataPelajaran,
    String? tahunAjaran,
    String? tanggalUjian,
    List<Map<String, dynamic>>? kunciJawaban,
  }) async {
    final body = <String, dynamic>{};
    if (kelas != null) body['kelas'] = kelas;
    if (mataPelajaran != null) body['mata_pelajaran'] = mataPelajaran;
    if (tahunAjaran != null) body['tahun_ajaran'] = tahunAjaran;
    if (tanggalUjian != null) body['tanggal_ujian'] = tanggalUjian;
    if (kunciJawaban != null) body['kunci_jawaban'] = kunciJawaban;
    final data = await ApiClient.put('/ujian/$ujianId', body);
    return UjianModel.fromJson(data['ujian'] as Map<String, dynamic>);
  }

  /// Hapus ujian (cascade ke kunci jawaban & penilaian terkait).
  Future<void> deleteUjian(int ujianId) async {
    await ApiClient.delete('/ujian/$ujianId');
  }
}
