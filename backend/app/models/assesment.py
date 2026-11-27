import enum
from datetime import datetime
from ..extensions import db


class StatusAssesment(enum.Enum):
    DIPROSES = 'Diproses'
    SELESAI = 'Selesai'


class Assesment(db.Model):
    """Model tabel ASSESMENT — hasil penilaian per siswa."""
    __tablename__ = 'assesment'

    assesment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ujian_id = db.Column(db.Integer, db.ForeignKey('ujian.ujian_id', ondelete='CASCADE'), nullable=False)
    nama_siswa = db.Column(db.String(255), nullable=False)
    nis_siswa = db.Column(db.String(50), nullable=False)
    total_benar = db.Column(db.Integer, nullable=False, default=0)
    total_salah = db.Column(db.Integer, nullable=False, default=0)
    nilai_akhir = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.Enum(StatusAssesment), nullable=False, default=StatusAssesment.DIPROSES)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relasi ke detail penilaian
    detail = db.relationship(
        'AssesmentDetail', backref='assesment', lazy='dynamic', cascade='all, delete-orphan'
    )

    def to_dict(self, include_detail=False) -> dict:
        """Serialisasi model ke dictionary."""
        data = {
            'assesment_id': self.assesment_id,
            'ujian_id': self.ujian_id,
            'nama_siswa': self.nama_siswa,
            'nis_siswa': self.nis_siswa,
            'total_benar': self.total_benar,
            'total_salah': self.total_salah,
            'nilai_akhir': self.nilai_akhir,
            'status': self.status.value if self.status else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        # Sertakan info ujian jika relasi sudah di-load
        if self.ujian:
            data['kelas'] = self.ujian.kelas
            data['mata_pelajaran'] = self.ujian.mata_pelajaran
            data['tanggal_ujian'] = self.ujian.tanggal_ujian.isoformat() if self.ujian.tanggal_ujian else None
        if include_detail:
            data['detail'] = [d.to_dict() for d in self.detail.order_by('nomor_soal')]
        return data

    def __repr__(self):
        return f'<Assesment {self.nama_siswa} ({self.nis_siswa})>'
