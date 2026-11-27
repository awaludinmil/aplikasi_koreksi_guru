from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from datetime import datetime
from ..extensions import db
from ..models.assesment import Assesment, StatusAssesment
from ..models.ujian import Ujian

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """
    GET /api/dashboard/stats
    Statistik rekap penilaian milik guru yang login.
    """
    user_id = int(get_jwt_identity())
    now = datetime.utcnow()

    # Query penilaian guru melalui tabel ujian (karena user_id ada di UJIAN)
    base_query = (
        db.session.query(Assesment)
        .join(Ujian, Assesment.ujian_id == Ujian.ujian_id)
        .filter(Ujian.user_id == user_id)
    )

    # 1. Total Siswa Dinilai (status selesai)
    total_siswa_dinilai = (
        base_query
        .filter(Assesment.status == StatusAssesment.SELESAI)
        .count()
    )

    # 2. Rata-rata nilai
    rata_rata_nilai = (
        base_query
        .filter(Assesment.status == StatusAssesment.SELESAI)
        .with_entities(func.avg(Assesment.nilai_akhir))
        .scalar()
    ) or 0.0

    # 3. Nilai Tertinggi
    nilai_tertinggi = (
        base_query
        .filter(Assesment.status == StatusAssesment.SELESAI)
        .with_entities(func.max(Assesment.nilai_akhir))
        .scalar()
    ) or 0.0

    from sqlalchemy import extract
    penilaian_bulan_ini = (
        base_query
        .filter(
            extract('year', Assesment.created_at) == now.year,
            extract('month', Assesment.created_at) == now.month
        )
        .count()
    )

    return jsonify({
        'total_siswa_dinilai': total_siswa_dinilai,
        'rata_rata_nilai': float(rata_rata_nilai),
        'nilai_tertinggi': float(nilai_tertinggi),
        'penilaian_bulan_ini': penilaian_bulan_ini
    }), 200

@dashboard_bp.route('/recent', methods=['GET'])
@jwt_required()
def get_recent():
    """
    GET /api/dashboard/recent
    Mengambil 5 penilaian terakhir milik guru.
    """
    user_id = int(get_jwt_identity())

    recent_assesments = (
        db.session.query(Assesment)
        .join(Ujian, Assesment.ujian_id == Ujian.ujian_id)
        .filter(Ujian.user_id == user_id)
        .order_by(Assesment.created_at.desc())
        .limit(5)
        .all()
    )

    result = []
    for a in recent_assesments:
        result.append({
            'assesment_id': a.assesment_id,
            'ujian_id': a.ujian_id,
            'nama_siswa': a.nama_siswa,
            'nis_siswa': a.nis_siswa,
            'total_benar': a.total_benar,
            'total_salah': a.total_salah,
            'nilai_akhir': a.nilai_akhir,
            'status': a.status.value if a.status else None,
            'kelas': a.ujian.kelas if a.ujian else None,
            'mata_pelajaran': a.ujian.mata_pelajaran if a.ujian else None,
            'tanggal_ujian': a.ujian.tanggal_ujian.isoformat() if (a.ujian and a.ujian.tanggal_ujian) else None,
            'created_at': a.created_at.isoformat() if a.created_at else None,
            'detail': []
        })

    return jsonify({'recent': result}), 200
