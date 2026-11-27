from ..extensions import db


class AssesmentDetail(db.Model):
    """Model tabel ASSESMENT_DETAIL — detail jawaban per soal dari hasil OCR."""
    __tablename__ = 'assesment_detail'

    detail_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    assesment_id = db.Column(
        db.Integer, db.ForeignKey('assesment.assesment_id', ondelete='CASCADE'), nullable=False
    )
    nomor_soal = db.Column(db.Integer, nullable=False)
    jawaban_siswa = db.Column(db.String(5), nullable=False)  # Hasil OCR atau input manual
    is_benar = db.Column(db.Boolean, nullable=False, default=False)

    def to_dict(self) -> dict:
        """Serialisasi model ke dictionary."""
        return {
            'detail_id': self.detail_id,
            'assesment_id': self.assesment_id,
            'nomor_soal': self.nomor_soal,
            'jawaban_siswa': self.jawaban_siswa,
            'is_benar': self.is_benar,
        }

    def __repr__(self):
        status = 'Benar' if self.is_benar else 'Salah'
        return f'<Detail No.{self.nomor_soal}: {self.jawaban_siswa} ({status})>'
