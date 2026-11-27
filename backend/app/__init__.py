import os
import logging
from flask import Flask, request
from .config import config_by_name
from .extensions import db, migrate, jwt, cors


def create_app(config_name=None):
    """Flask App Factory."""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name['default']))

    # Setup Logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Inisialisasi extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(
        app,
        resources={r"/*": {"origins": "*"}},
        supports_credentials=True,
        allow_headers="*",
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"]
    )

    # Import semua models agar Flask-Migrate bisa mendeteksinya
    from .models import user, ujian, kunci_jawaban, assesment, assesment_detail  # noqa: F401

    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.dashboard import dashboard_bp
    from .routes.ujian import ujian_bp
    from .routes.assesment import assesment_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(ujian_bp, url_prefix='/api/ujian')
    app.register_blueprint(assesment_bp, url_prefix='/api/assesment')

    # Request Logging Middleware
    @app.before_request
    def log_request_info():
        # Handle preflight OPTIONS langsung
        if request.method == 'OPTIONS':
            return

        app.logger.info(f"Incoming Request: {request.method} {request.path}")
        if request.is_json:
            # Hindari logging password
            body = request.get_json(silent=True) or {}
            safe_body = {k: v for k, v in body.items() if 'password' not in k.lower()}
            app.logger.info(f"Body: {safe_body}")

    @app.after_request
    def log_response_info(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        if request.method != 'OPTIONS':
            app.logger.info(f"Response: {response.status}")
        return response

    # Health check endpoint
    @app.route('/api/health')
    def health():
        return {'status': 'ok', 'message': 'Backend Skripsi OCR berjalan normal'}, 200

    return app
