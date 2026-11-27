from ..extensions import db


class KunciJawaban(db.Model):
    """Model tabel KUNCI_JAWABAN — kunci jawaban per nomor soal untuk satu ujian."""
    __tablename__ = 'kunci_jawaban'

    kunci_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ujian_id = db.Column(db.Integer, db.ForeignKey('ujian.ujian_id', ondelete='CASCADE'), nullable=False)
    nomor_soal = db.Column(db.Integer, nullable=False)
    kunci = db.Column(db.String(5), nullable=False)  # A/B/C/D

    def to_dict(self) -> dict:
        """Serialisasi model ke dictionary."""
        return {
            'kunci_id': self.kunci_id,
            'ujian_id': self.ujian_id,
            'nomor_soal': self.nomor_soal,
            'kunci': self.kunci,
        }

    def __repr__(self):
        return f'<KunciJawaban No.{self.nomor_soal}: {self.kunci}>'
