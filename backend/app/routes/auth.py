from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity
)
from ..extensions import db
from ..models.user import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    POST /api/auth/register
    Daftarkan akun guru baru.
    Body: { username, full_name, password, confirm_password }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body tidak valid'}), 400

    # Validasi field wajib
    required = ['username', 'full_name', 'password', 'confirm_password']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'error': f'Field berikut wajib diisi: {", ".join(missing)}'}), 400

    if data['password'] != data['confirm_password']:
        return jsonify({'error': 'Password dan konfirmasi password tidak cocok'}), 400

    if len(data['password']) < 8:
        return jsonify({'error': 'Password minimal 8 karakter'}), 400

    # Cek username sudah terdaftar
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username sudah digunakan, pilih username lain'}), 409

    # Buat user baru
    user = User(username=data['username'], full_name=data['full_name'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(identity=str(user.user_id))
    return jsonify({
        'message': 'Akun guru berhasil dibuat',
        'access_token': access_token,
        'user': user.to_dict()
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    POST /api/auth/login
    Login guru dan return JWT access token.
    Body: { username, password }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body tidak valid'}), 400

    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': 'Username dan password wajib diisi'}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Username atau password salah'}), 401

    access_token = create_access_token(identity=str(user.user_id))
    return jsonify({
        'message': 'Login berhasil',
        'access_token': access_token,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """
    GET /api/auth/profile
    Ambil profil guru yang sedang login.
    Header: Authorization: Bearer <token>
    """
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    return jsonify({'user': user.to_dict()}), 200


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """
    PUT /api/auth/profile
    Edit profil guru (full_name, username).
    Body: { full_name?, username? }
    """
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body tidak valid'}), 400

    if 'full_name' in data and data['full_name'].strip():
        user.full_name = data['full_name'].strip()

    if 'username' in data and data['username'].strip():
        new_username = data['username'].strip()
        if new_username != user.username:
            if User.query.filter_by(username=new_username).first():
                return jsonify({'error': 'Username sudah digunakan'}), 409
            user.username = new_username

    db.session.commit()
    return jsonify({'message': 'Profil berhasil diperbarui', 'user': user.to_dict()}), 200


@auth_bp.route('/change-password', methods=['PUT'])
@jwt_required()
def change_password():
    """
    PUT /api/auth/change-password
    Ganti password guru.
    Body: { old_password, new_password, confirm_new_password }
    """
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body tidak valid'}), 400

    required = ['old_password', 'new_password', 'confirm_new_password']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'error': f'Field berikut wajib diisi: {", ".join(missing)}'}), 400

    if not user.check_password(data['old_password']):
        return jsonify({'error': 'Password lama salah'}), 401

    if data['new_password'] != data['confirm_new_password']:
        return jsonify({'error': 'Password baru dan konfirmasi tidak cocok'}), 400

    if len(data['new_password']) < 8:
        return jsonify({'error': 'Password baru minimal 8 karakter'}), 400

    user.set_password(data['new_password'])
    db.session.commit()
    return jsonify({'message': 'Password berhasil diubah'}), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    POST /api/auth/logout
    Logout guru (client wajib hapus token di sisi Flutter).
    """
    return jsonify({'message': 'Logout berhasil. Hapus token di sisi aplikasi.'}), 200
