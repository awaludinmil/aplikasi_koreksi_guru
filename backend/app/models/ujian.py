from datetime import datetime
from ..extensions import db


class Ujian(db.Model):
    """Model tabel UJIAN — master data ujian yang dibuat guru."""
    __tablename__ = 'ujian'

    ujian_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    kelas = db.Column(db.String(50), nullable=False)
    mata_pelajaran = db.Column(db.String(100), nullable=False)
    tahun_ajaran = db.Column(db.String(50), nullable=False)
    tanggal_ujian = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relasi ke kunci jawaban dan penilaian
    kunci_jawaban = db.relationship(
        'KunciJawaban', backref='ujian', lazy='dynamic', cascade='all, delete-orphan'
    )
    assesment = db.relationship(
        'Assesment', backref='ujian', lazy='dynamic', cascade='all, delete-orphan'
    )

    def to_dict(self, include_kunci=False) -> dict:
        """Serialisasi model ke dictionary."""
        data = {
            'ujian_id': self.ujian_id,
            'user_id': self.user_id,
            'kelas': self.kelas,
            'mata_pelajaran': self.mata_pelajaran,
            'tahun_ajaran': self.tahun_ajaran,
            'tanggal_ujian': self.tanggal_ujian.isoformat() if self.tanggal_ujian else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_kunci:
            data['kunci_jawaban'] = [k.to_dict() for k in self.kunci_jawaban.order_by('nomor_soal')]
        return data

    def __repr__(self):
        return f'<Ujian {self.mata_pelajaran} - {self.kelas}>'
