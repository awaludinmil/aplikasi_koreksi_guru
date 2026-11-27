from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_
from ..extensions import db
from ..models.assesment import Assesment, StatusAssesment
from ..models.assesment_detail import AssesmentDetail
from ..models.ujian import Ujian
from ..models.kunci_jawaban import KunciJawaban
from ..utils.ocr import process_ocr_image

assesment_bp = Blueprint('assesment', __name__)


def _get_user_assesment_query(user_id: int):
    """Helper — query penilaian yang hanya milik guru (via join ujian)."""
    return (
        db.session.query(Assesment)
        .join(Ujian, Assesment.ujian_id == Ujian.ujian_id)
        .filter(Ujian.user_id == user_id)
    )


def _hitung_nilai(total_benar: int, total_soal: int) -> float:
    """Hitung nilai akhir skala 0–100."""
    if total_soal == 0:
        return 0.0
    return round((total_benar / total_soal) * 100, 2)


@assesment_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_assesment():
    """
    GET /api/assesment/
    Daftar penilaian milik guru dengan filter, search, dan paginasi.
    Query params:
      - q        : cari nama siswa / NIS
      - kelas    : filter kelas
      - status   : Diproses | Selesai
      - page     : halaman (default 1)
      - per_page : jumlah per halaman (default 10)
    """
    user_id = int(get_jwt_identity())
    query = _get_user_assesment_query(user_id)

    # Search nama atau NIS
    q = request.args.get('q', '').strip()
    if q:
        query = query.filter(
            or_(
                Assesment.nama_siswa.like(f'%{q}%'),
                Assesment.nis_siswa.like(f'%{q}%'),
            )
        )

    # Filter kelas (via join ujian)
    kelas = request.args.get('kelas', '').strip()
    if kelas:
        query = query.filter(Ujian.kelas == kelas)

    # Filter status
    status_param = request.args.get('status', '').strip()
    if status_param:
        try:
            status_enum = StatusAssesment(status_param)
            query = query.filter(Assesment.status == status_enum)
        except ValueError:
            return jsonify({'error': 'Status tidak valid. Gunakan: Diproses atau Selesai'}), 400

    # Urutkan terbaru dulu
    query = query.order_by(Assesment.created_at.desc())

    # Paginasi
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'total_pages': pagination.pages,
        'assesment': [a.to_dict() for a in pagination.items]
    }), 200


@assesment_bp.route('/', methods=['POST'])
@jwt_required()
def create_assesment():
    """
    POST /api/assesment/
    Buat penilaian baru (simpan hasil OCR + data siswa).
    Body: {
        ujian_id,
        nama_siswa,
        nis_siswa,
        detail: [{ nomor_soal, jawaban_siswa }, ...]
    }
    Sistem otomatis mencocokkan dengan kunci jawaban dan menghitung nilai.
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body tidak valid'}), 400

    required = ['ujian_id', 'nama_siswa', 'nis_siswa', 'detail']
    missing = [f for f in required if not data.get(f) and data.get(f) != 0]
    if missing:
        return jsonify({'error': f'Field wajib: {", ".join(missing)}'}), 400

    # Pastikan ujian milik guru ini
    ujian = Ujian.query.filter_by(ujian_id=data['ujian_id'], user_id=user_id).first()
    if not ujian:
        return jsonify({'error': 'Ujian tidak ditemukan atau bukan milik Anda'}), 404

    # Ambil kunci jawaban ujian ini
    kunci_map = {
        kj.nomor_soal: kj.kunci
        for kj in KunciJawaban.query.filter_by(ujian_id=ujian.ujian_id).all()
    }
    if not kunci_map:
        return jsonify({'error': 'Ujian belum memiliki kunci jawaban'}), 400

    detail_list = data.get('detail', [])
    if not isinstance(detail_list, list) or len(detail_list) == 0:
        return jsonify({'error': 'Detail jawaban siswa wajib diisi'}), 400

    # Buat assesment header (sementara, nilai dihitung setelah proses detail)
    assesment = Assesment(
        ujian_id=ujian.ujian_id,
        nama_siswa=data['nama_siswa'].strip(),
        nis_siswa=str(data['nis_siswa']).strip(),
        status=StatusAssesment.DIPROSES,
    )
    db.session.add(assesment)
    db.session.flush()  # Dapatkan assesment_id

    total_benar = 0
    total_salah = 0

    for item in detail_list:
        nomor = item.get('nomor_soal')
        jawaban = str(item.get('jawaban_siswa', '')).strip().upper()
        if not nomor:
            db.session.rollback()
            return jsonify({'error': 'nomor_soal wajib ada di setiap item detail'}), 400

        kunci = kunci_map.get(nomor)
        is_benar = (kunci is not None) and (jawaban == kunci)

        if is_benar:
            total_benar += 1
        else:
            total_salah += 1

        detail = AssesmentDetail(
            assesment_id=assesment.assesment_id,
            nomor_soal=nomor,
            jawaban_siswa=jawaban,
            is_benar=is_benar,
        )
        db.session.add(detail)

    # Update rekap
    total_soal = total_benar + total_salah
    assesment.total_benar = total_benar
    assesment.total_salah = total_salah
    assesment.nilai_akhir = _hitung_nilai(total_benar, total_soal)
    assesment.status = StatusAssesment.SELESAI

    db.session.commit()
    return jsonify({
        'message': 'Penilaian berhasil disimpan',
        'assesment': assesment.to_dict(include_detail=True)
    }), 201


@assesment_bp.route('/<int:assesment_id>', methods=['GET'])
@jwt_required()
def get_assesment(assesment_id):
    """
    GET /api/assesment/<assesment_id>
    Detail penilaian beserta jawaban per soal.
    """
    user_id = int(get_jwt_identity())
    assesment = _get_user_assesment_query(user_id).filter(
        Assesment.assesment_id == assesment_id
    ).first_or_404()
    return jsonify({'assesment': assesment.to_dict(include_detail=True)}), 200


@assesment_bp.route('/<int:assesment_id>', methods=['PUT'])
@jwt_required()
def update_assesment(assesment_id):
    """
    PUT /api/assesment/<assesment_id>
    Edit penilaian: nama siswa, NIS, dan/atau jawaban per soal.
    Body: {
        nama_siswa?,
        nis_siswa?,
        detail?: [{ nomor_soal, jawaban_siswa }, ...]
    }
    Jika detail disertakan, sistem otomatis hitung ulang nilai.
    """
    user_id = int(get_jwt_identity())
    assesment = _get_user_assesment_query(user_id).filter(
        Assesment.assesment_id == assesment_id
    ).first_or_404()

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body tidak valid'}), 400

    if 'nama_siswa' in data and data['nama_siswa'].strip():
        assesment.nama_siswa = data['nama_siswa'].strip()

    if 'nis_siswa' in data and str(data['nis_siswa']).strip():
        assesment.nis_siswa = str(data['nis_siswa']).strip()

    # Jika ada update jawaban (edit manual hasil OCR)
    if 'detail' in data:
        detail_list = data['detail']
        if not isinstance(detail_list, list) or len(detail_list) == 0:
            return jsonify({'error': 'detail harus berupa list dan tidak kosong'}), 400

        # Ambil kunci jawaban
        kunci_map = {
            kj.nomor_soal: kj.kunci
            for kj in KunciJawaban.query.filter_by(ujian_id=assesment.ujian_id).all()
        }

        # Hapus detail lama, ganti baru
        AssesmentDetail.query.filter_by(assesment_id=assesment_id).delete()

        total_benar = 0
        total_salah = 0

        for item in detail_list:
            nomor = item.get('nomor_soal')
            jawaban = str(item.get('jawaban_siswa', '')).strip().upper()
            kunci = kunci_map.get(nomor)
            is_benar = (kunci is not None) and (jawaban == kunci)

            if is_benar:
                total_benar += 1
            else:
                total_salah += 1

            d = AssesmentDetail(
                assesment_id=assesment_id,
                nomor_soal=nomor,
                jawaban_siswa=jawaban,
                is_benar=is_benar,
            )
            db.session.add(d)

        total_soal = total_benar + total_salah
        assesment.total_benar = total_benar
        assesment.total_salah = total_salah
        assesment.nilai_akhir = _hitung_nilai(total_benar, total_soal)
        assesment.status = StatusAssesment.SELESAI

    db.session.commit()
    return jsonify({
        'message': 'Penilaian berhasil diperbarui',
        'assesment': assesment.to_dict(include_detail=True)
    }), 200


@assesment_bp.route('/<int:assesment_id>', methods=['DELETE'])
@jwt_required()
def delete_assesment(assesment_id):
    """
    DELETE /api/assesment/<assesment_id>
    Hapus penilaian beserta semua detail jawaban (cascade).
    """
    user_id = int(get_jwt_identity())
    assesment = _get_user_assesment_query(user_id).filter(
        Assesment.assesment_id == assesment_id
    ).first_or_404()
    db.session.delete(assesment)
    db.session.commit()
    return jsonify({'message': 'Penilaian berhasil dihapus'}), 200


@assesment_bp.route('/ocr', methods=['POST'])
@jwt_required()
def ocr_jawaban():
    """
    POST /api/assesment/ocr
    Upload foto lembar jawaban siswa → proses OCR → return jawaban per nomor soal.

    Form-data:
      - image : file gambar (JPG/PNG, maks 10MB)
      - jumlah_soal : jumlah soal yang dikoreksi (int)

    Return:
      {
        "ocr_result": [
          { "nomor_soal": 1, "jawaban_siswa": "A" },
          { "nomor_soal": 2, "jawaban_siswa": "C" },
          ...
        ],
        "is_dummy": true  ← true jika pakai stub/dummy
      }
    """
    if 'image' not in request.files:
        return jsonify({'error': 'File gambar (field: image) wajib disertakan'}), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({'error': 'Tidak ada file yang dipilih'}), 400

    allowed_extensions = {'jpg', 'jpeg', 'png'}
    ext = image_file.filename.rsplit('.', 1)[-1].lower()
    if ext not in allowed_extensions:
        return jsonify({'error': 'Format file tidak didukung. Gunakan JPG atau PNG'}), 400

    # Validasi ukuran (maks 10MB)
    image_file.seek(0, 2)  # Seek ke akhir
    file_size = image_file.tell()
    image_file.seek(0)
    if file_size > 10 * 1024 * 1024:
        return jsonify({'error': 'Ukuran file melebihi batas 10MB'}), 400

    jumlah_soal = request.form.get('jumlah_soal', 10, type=int)

    # Proses OCR (stub/dummy atau Tesseract jika tersedia)
    ocr_result, is_dummy = process_ocr_image(image_file, jumlah_soal)

    return jsonify({
        'ocr_result': ocr_result,
        'is_dummy': is_dummy,
        'message': (
            'Hasil OCR simulasi (dummy). Silakan periksa dan edit jika perlu.'
            if is_dummy else
            'Hasil OCR berhasil diproses. Silakan periksa dan edit jika perlu.'
        )
    }), 200


@assesment_bp.route('/predict', methods=['POST', 'OPTIONS'])
@jwt_required(optional=True)
def predict_jawaban_ai():
    """
    POST /api/assesment/predict
    Upload foto lembar soal siswa → OpenCV Tracking Nomor & Opsi → ResNet50 CNN Classification.

    Form-data:
      - image       : file gambar lembar soal (JPG/PNG, maks 15MB)
      - ujian_id    : (opsional) ID ujian untuk pencocokan kunci jawaban
      - threshold   : (opsional) ambang batas deteksi terpilih (default: 0.40)
    """
    if request.method == 'OPTIONS':
        return ('', 204)

    from ..utils.detector import track_and_predict_questions

    if 'images' not in request.files and 'image' not in request.files:
        return jsonify({'error': 'File gambar (field: images) wajib disertakan'}), 400

    image_files = request.files.getlist('images')
    if not image_files:
        # Fallback to 'image' for backward compatibility
        if 'image' in request.files:
            image_files = request.files.getlist('image')
            
    if not image_files or all(f.filename == '' for f in image_files):
        return jsonify({'error': 'Tidak ada file yang dipilih'}), 400

    if len(image_files) > 4:
        return jsonify({'error': 'Maksimal 4 gambar yang diizinkan'}), 400

    allowed_extensions = {'jpg', 'jpeg', 'png', 'webp'}
    threshold = request.form.get('threshold', 0.40, type=float)
    ujian_id = request.form.get('ujian_id', type=int)
    
    all_results = []
    all_annotated_images = []
    
    current_q_num = 1
    try:
        for image_file in image_files:
            ext = image_file.filename.rsplit('.', 1)[-1].lower()
            if ext not in allowed_extensions:
                return jsonify({'error': f'Format file tidak didukung: {image_file.filename}. Gunakan JPG, PNG, atau WEBP'}), 400

            # Validasi ukuran (maks 15MB per gambar)
            image_file.seek(0, 2)
            file_size = image_file.tell()
            image_file.seek(0)
            if file_size > 15 * 1024 * 1024:
                return jsonify({'error': f'Ukuran file {image_file.filename} melebihi batas 15MB'}), 400

            # Jalankan pipeline OpenCV Tracking + ResNet50 Inference dengan penomoran berlanjut antar-halaman
            detection_result = track_and_predict_questions(
                image_file,
                threshold=threshold,
                start_question_number=current_q_num
            )
            img_results = detection_result.get('results', [])
            all_results.extend(img_results)
            current_q_num += len(img_results)

            if 'annotated_image' in detection_result:
                all_annotated_images.append(detection_result['annotated_image'])
                
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Gagal memproses gambar: {str(e)}'}), 500

    # Jika ujian_id disertakan, lakukan pencocokan otomatis dengan kunci jawaban
    evaluasi_ujian = None
    if ujian_id:
        ujian = Ujian.query.filter_by(ujian_id=ujian_id).first()
        if ujian:
            kunci_map = {
                kj.nomor_soal: kj.kunci
                for kj in KunciJawaban.query.filter_by(ujian_id=ujian.ujian_id).all()
            }
            total_benar = 0
            total_salah = 0
            detail_evaluasi = []

            for r in all_results:
                nomor = r['nomor_soal']
                jawaban_siswa = r['jawaban_terpilih']
                kunci = kunci_map.get(nomor)

                is_benar = (kunci is not None) and (jawaban_siswa == kunci)
                if is_benar:
                    total_benar += 1
                else:
                    total_salah += 1

                detail_evaluasi.append({
                    'nomor_soal': nomor,
                    'jawaban_siswa': jawaban_siswa,
                    'kunci_jawaban': kunci,
                    'is_benar': is_benar
                })

            total_soal = total_benar + total_salah
            nilai_akhir = _hitung_nilai(total_benar, total_soal)

            evaluasi_ujian = {
                'ujian_id': ujian.ujian_id,
                'judul_ujian': f"{ujian.mata_pelajaran} - {ujian.kelas}",
                'total_benar': total_benar,
                'total_salah': total_salah,
                'nilai_akhir': nilai_akhir,
                'detail': detail_evaluasi
            }

    response_payload = {
        'success': True,
        'message': f"Prediksi berhasil diproses untuk {len(image_files)} gambar",
        'total_soal_terdeteksi': len(all_results),
        'results': all_results,
        'annotated_images': all_annotated_images
    }

    if evaluasi_ujian:
        response_payload['evaluasi_ujian'] = evaluasi_ujian

    return jsonify(response_payload), 200
