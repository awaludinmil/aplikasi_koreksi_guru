class AssesmentDetailModel {
  final int detailId;
  final int assesmentId;
  final int nomorSoal;
  final String jawabanSiswa;
  final bool isBenar;

  AssesmentDetailModel({
    required this.detailId,
    required this.assesmentId,
    required this.nomorSoal,
    required this.jawabanSiswa,
    required this.isBenar,
  });

  factory AssesmentDetailModel.fromJson(Map<String, dynamic> json) {
    return AssesmentDetailModel(
      detailId: json['detail_id'] as int,
      assesmentId: json['assesment_id'] as int,
      nomorSoal: json['nomor_soal'] as int,
      jawabanSiswa: json['jawaban_siswa'] as String,
      isBenar: json['is_benar'] as bool,
    );
  }

  Map<String, dynamic> toJson() => {
        'nomor_soal': nomorSoal,
        'jawaban_siswa': jawabanSiswa,
      };
}

class AssesmentModel {
  final int assesmentId;
  final int ujianId;
  final String namaSiswa;
  final String nisSiswa;
  final int totalBenar;
  final int totalSalah;
  final double nilaiAkhir;
  final String status;
  final String? kelas;
  final String? mataPelajaran;
  final String? tanggalUjian;
  final String? createdAt;
  final List<AssesmentDetailModel> detail;

  AssesmentModel({
    required this.assesmentId,
    required this.ujianId,
    required this.namaSiswa,
    required this.nisSiswa,
    required this.totalBenar,
    required this.totalSalah,
    required this.nilaiAkhir,
    required this.status,
    this.kelas,
    this.mataPelajaran,
    this.tanggalUjian,
    this.createdAt,
    this.detail = const [],
  });

  bool get isSelesai => status == 'Selesai';

  factory AssesmentModel.fromJson(Map<String, dynamic> json) {
    return AssesmentModel(
      assesmentId: json['assesment_id'] as int,
      ujianId: json['ujian_id'] as int,
      namaSiswa: json['nama_siswa'] as String,
      nisSiswa: json['nis_siswa'] as String,
      totalBenar: json['total_benar'] as int,
      totalSalah: json['total_salah'] as int,
      nilaiAkhir: (json['nilai_akhir'] as num).toDouble(),
      status: json['status'] as String,
      kelas: json['kelas'] as String?,
      mataPelajaran: json['mata_pelajaran'] as String?,
      tanggalUjian: json['tanggal_ujian'] as String?,
      createdAt: json['created_at'] as String?,
      detail: (json['detail'] as List<dynamic>? ?? [])
          .map((e) => AssesmentDetailModel.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}
