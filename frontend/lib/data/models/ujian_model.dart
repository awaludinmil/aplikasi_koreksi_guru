class KunciJawabanModel {
  final int? kunciId;
  final int nomorSoal;
  final String kunci;

  KunciJawabanModel({
    this.kunciId,
    required this.nomorSoal,
    required this.kunci,
  });

  factory KunciJawabanModel.fromJson(Map<String, dynamic> json) {
    return KunciJawabanModel(
      kunciId: json['kunci_id'] as int?,
      nomorSoal: json['nomor_soal'] as int,
      kunci: json['kunci'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
        'nomor_soal': nomorSoal,
        'kunci': kunci,
      };
}

class UjianModel {
  final int ujianId;
  final int userId;
  final String kelas;
  final String mataPelajaran;
  final String tahunAjaran;
  final String tanggalUjian;
  final List<KunciJawabanModel> kunciJawaban;

  UjianModel({
    required this.ujianId,
    required this.userId,
    required this.kelas,
    required this.mataPelajaran,
    required this.tahunAjaran,
    required this.tanggalUjian,
    this.kunciJawaban = const [],
  });

  factory UjianModel.fromJson(Map<String, dynamic> json) {
    return UjianModel(
      ujianId: json['ujian_id'] as int,
      userId: json['user_id'] as int,
      kelas: json['kelas'] as String,
      mataPelajaran: json['mata_pelajaran'] as String,
      tahunAjaran: json['tahun_ajaran'] as String,
      tanggalUjian: json['tanggal_ujian'] as String,
      kunciJawaban: (json['kunci_jawaban'] as List<dynamic>? ?? [])
          .map((e) => KunciJawabanModel.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }

  /// Label singkat untuk dropdown pemilihan ujian
  String get label => '$mataPelajaran - $kelas - $tanggalUjian';
}
