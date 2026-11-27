from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db


class User(db.Model):
    """Model tabel USERS — akun guru."""
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    full_name = db.Column(db.String(265), nullable=False)
    password = db.Column(db.String(255), nullable=False)

    # Relasi ke ujian
    ujian = db.relationship('Ujian', backref='guru', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password: str):
        """Hash dan simpan password."""
        self.password = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Cek password dengan hash yang tersimpan."""
        return check_password_hash(self.password, password)

    def to_dict(self) -> dict:
        """Serialisasi model ke dictionary."""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'full_name': self.full_name,
        }

    def __repr__(self):
        return f'<User {self.username}>'
