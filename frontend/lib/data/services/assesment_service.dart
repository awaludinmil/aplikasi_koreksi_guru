import 'dart:io';
import 'package:dio/dio.dart';
import '../models/assesment_model.dart';
import 'api_client.dart';

class AssesmentService {
  /// Ambil daftar penilaian dengan filter opsional dan paginasi.
  Future<Map<String, dynamic>> getRiwayat({
    String? q,
    String? kelas,
    String? status,
    int page = 1,
    int perPage = 10,
  }) async {
    final query = <String, dynamic>{'page': page, 'per_page': perPage};
    if (q != null && q.isNotEmpty) query['q'] = q;
    if (kelas != null && kelas.isNotEmpty) query['kelas'] = kelas;
    if (status != null && status.isNotEmpty) query['status'] = status;

    final data = await ApiClient.get('/assesment/', query: query);
    return {
      'total': data['total'] as int,
      'page': data['page'] as int,
      'total_pages': data['total_pages'] as int,
      'assesment': (data['assesment'] as List<dynamic>)
          .map((e) => AssesmentModel.fromJson(e as Map<String, dynamic>))
          .toList(),
    };
  }

  /// Ambil detail satu penilaian beserta jawaban per soal.
  Future<AssesmentModel> getDetail(int assesmentId) async {
    final data = await ApiClient.get('/assesment/$assesmentId');
    return AssesmentModel.fromJson(data['assesment'] as Map<String, dynamic>);
  }

  /// Buat penilaian baru — nilai dihitung otomatis oleh backend.
  /// [detail] : list of { 'nomor_soal': int, 'jawaban_siswa': 'A'|'B'|'C'|'D' }
  Future<AssesmentModel> createAssesment({
    required int ujianId,
    required String namaSiswa,
    required String nisSiswa,
    required List<Map<String, dynamic>> detail,
  }) async {
    final data = await ApiClient.post('/assesment/', {
      'ujian_id': ujianId,
      'nama_siswa': namaSiswa.trim(),
      'nis_siswa': nisSiswa.trim(),
      'detail': detail,
    });
    return AssesmentModel.fromJson(data['assesment'] as Map<String, dynamic>);
  }

  /// Edit penilaian — nama siswa, NIS, dan/atau jawaban per soal.
  /// Jika [detail] disertakan, nilai dihitung ulang otomatis.
  Future<AssesmentModel> updateAssesment(
    int assesmentId, {
    String? namaSiswa,
    String? nisSiswa,
    List<Map<String, dynamic>>? detail,
  }) async {
    final body = <String, dynamic>{};
    if (namaSiswa != null) body['nama_siswa'] = namaSiswa.trim();
    if (nisSiswa != null) body['nis_siswa'] = nisSiswa.trim();
    if (detail != null) body['detail'] = detail;
    final data = await ApiClient.put('/assesment/$assesmentId', body);
    return AssesmentModel.fromJson(data['assesment'] as Map<String, dynamic>);
  }

  /// Hapus penilaian dan semua detail jawaban (cascade).
  Future<void> deleteAssesment(int assesmentId) async {
    await ApiClient.delete('/assesment/$assesmentId');
  }

  /// Upload foto lembar jawaban (multi) → backend proses OCR + AI ResNet50 → return prediksi & evaluasi.
  Future<Map<String, dynamic>> predictLembarSoal({
    required List<Map<String, dynamic>> imageDataList, // [{'bytes': List<int>, 'filename': String}]
    required int ujianId,
    double threshold = 0.40,
  }) async {
    final imageFiles = imageDataList.map((data) {
      return MultipartFile.fromBytes(
        data['bytes'] as List<int>,
        filename: data['filename'] as String,
      );
    }).toList();

    final data = await ApiClient.postMultipartBytes(
      '/assesment/predict',
      imageFiles: imageFiles,
      fields: {
        'ujian_id': ujianId.toString(),
        'threshold': threshold.toString(),
      },
    );
    return data;
  }

  /// Upload foto lembar jawaban → backend proses OCR → return jawaban per soal (legacy fallback).
  /// Return list of { 'nomor_soal': int, 'jawaban_siswa': String }
  Future<Map<String, dynamic>> uploadOcr({
    required File imageFile,
    required int jumlahSoal,
  }) async {
    final data = await ApiClient.postMultipart(
      '/assesment/ocr',
      imageFile: imageFile,
      fields: {'jumlah_soal': jumlahSoal.toString()},
    );
    return data;
  }
}
