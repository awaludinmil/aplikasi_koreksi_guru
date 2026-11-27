from datetime import date
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models.ujian import Ujian
from ..models.kunci_jawaban import KunciJawaban

ujian_bp = Blueprint('ujian', __name__)


@ujian_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_ujian():
    """
    GET /api/ujian/
    Ambil semua ujian milik guru yang login.
    """
    user_id = int(get_jwt_identity())
    ujian_list = Ujian.query.filter_by(user_id=user_id).order_by(Ujian.created_at.desc()).all()
    return jsonify({
        'total': len(ujian_list),
        'ujian': [u.to_dict(include_kunci=True) for u in ujian_list]
    }), 200


@ujian_bp.route('/', methods=['POST'])
@jwt_required()
def create_ujian():
    """
    POST /api/ujian/
    Buat ujian baru beserta kunci jawaban.
    Body: {
        kelas, mata_pelajaran, tahun_ajaran, tanggal_ujian,
        kunci_jawaban: [{ nomor_soal, kunci }, ...]
    }
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body tidak valid'}), 400

    # Validasi field ujian
    required = ['kelas', 'mata_pelajaran', 'tahun_ajaran', 'tanggal_ujian', 'kunci_jawaban']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'error': f'Field wajib: {", ".join(missing)}'}), 400

    kunci_list = data.get('kunci_jawaban', [])
    if not isinstance(kunci_list, list) or len(kunci_list) == 0:
        return jsonify({'error': 'Kunci jawaban harus berupa list dan minimal 1 soal'}), 400

    # Parse tanggal
    try:
        tanggal = date.fromisoformat(data['tanggal_ujian'])
    except ValueError:
        return jsonify({'error': 'Format tanggal_ujian tidak valid (gunakan YYYY-MM-DD)'}), 400

    # Buat ujian
    ujian = Ujian(
        user_id=user_id,
        kelas=data['kelas'],
        mata_pelajaran=data['mata_pelajaran'],
        tahun_ajaran=data['tahun_ajaran'],
        tanggal_ujian=tanggal,
    )
    db.session.add(ujian)
    db.session.flush()  # Dapatkan ujian_id sebelum commit

    # Buat kunci jawaban
    valid_kunci = {'A', 'B', 'C', 'D', 'E'}
    for item in kunci_list:
        nomor = item.get('nomor_soal')
        kunci = str(item.get('kunci', '')).strip().upper()
        if not nomor or kunci not in valid_kunci:
            db.session.rollback()
            return jsonify({
                'error': f'Kunci jawaban tidak valid di nomor {nomor}. Kunci harus A/B/C/D/E'
            }), 400
        kj = KunciJawaban(ujian_id=ujian.ujian_id, nomor_soal=nomor, kunci=kunci)
        db.session.add(kj)

    db.session.commit()
    return jsonify({
        'message': 'Ujian dan kunci jawaban berhasil disimpan',
        'ujian': ujian.to_dict(include_kunci=True)
    }), 201


@ujian_bp.route('/<int:ujian_id>', methods=['GET'])
@jwt_required()
def get_ujian(ujian_id):
    """
    GET /api/ujian/<ujian_id>
    Detail ujian beserta kunci jawaban.
    """
    user_id = int(get_jwt_identity())
    ujian = Ujian.query.filter_by(ujian_id=ujian_id, user_id=user_id).first_or_404()
    return jsonify({'ujian': ujian.to_dict(include_kunci=True)}), 200


@ujian_bp.route('/<int:ujian_id>', methods=['PUT'])
@jwt_required()
def update_ujian(ujian_id):
    """
    PUT /api/ujian/<ujian_id>
    Edit ujian dan/atau kunci jawaban.
    Body: { kelas?, mata_pelajaran?, tahun_ajaran?, tanggal_ujian?, kunci_jawaban? }
    """
    user_id = int(get_jwt_identity())
    ujian = Ujian.query.filter_by(ujian_id=ujian_id, user_id=user_id).first_or_404()
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body tidak valid'}), 400

    # Update field ujian
    if 'kelas' in data:
        ujian.kelas = data['kelas']
    if 'mata_pelajaran' in data:
        ujian.mata_pelajaran = data['mata_pelajaran']
    if 'tahun_ajaran' in data:
        ujian.tahun_ajaran = data['tahun_ajaran']
    if 'tanggal_ujian' in data:
        try:
            ujian.tanggal_ujian = date.fromisoformat(data['tanggal_ujian'])
        except ValueError:
            return jsonify({'error': 'Format tanggal_ujian tidak valid (YYYY-MM-DD)'}), 400

    # Update kunci jawaban jika disertakan
    if 'kunci_jawaban' in data:
        kunci_list = data['kunci_jawaban']
        if not isinstance(kunci_list, list) or len(kunci_list) == 0:
            return jsonify({'error': 'kunci_jawaban harus berupa list dan tidak kosong'}), 400

        # Hapus kunci lama dan ganti dengan yang baru
        KunciJawaban.query.filter_by(ujian_id=ujian_id).delete()
        valid_kunci = {'A', 'B', 'C', 'D', 'E'}
        for item in kunci_list:
            nomor = item.get('nomor_soal')
            kunci = str(item.get('kunci', '')).strip().upper()
            if not nomor or kunci not in valid_kunci:
                db.session.rollback()
                return jsonify({'error': f'Kunci tidak valid di nomor {nomor}'}), 400
            kj = KunciJawaban(ujian_id=ujian_id, nomor_soal=nomor, kunci=kunci)
            db.session.add(kj)

    db.session.commit()
    return jsonify({
        'message': 'Ujian berhasil diperbarui',
        'ujian': ujian.to_dict(include_kunci=True)
    }), 200


@ujian_bp.route('/<int:ujian_id>', methods=['DELETE'])
@jwt_required()
def delete_ujian(ujian_id):
    """
    DELETE /api/ujian/<ujian_id>
    Hapus ujian beserta kunci jawaban dan semua penilaian terkait (cascade).
    """
    user_id = int(get_jwt_identity())
    ujian = Ujian.query.filter_by(ujian_id=ujian_id, user_id=user_id).first_or_404()
    db.session.delete(ujian)
    db.session.commit()
    return jsonify({'message': 'Ujian berhasil dihapus'}), 200
