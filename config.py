import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'bbms-secret-key-change-in-production')

    # ⚠️  NEVER hardcode credentials. Set DATABASE_URL in your .env or hosting env vars.
    # Example: mysql+pymysql://user:pass@host:port/dbname
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///bbms_local.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.environ.get('SQLALCHEMY_ECHO', 'false').lower() == 'true'
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 60,
        "pool_pre_ping": True,
    }

    # Only add SSL connect_args when DATABASE_URL points to TiDB/MySQL (not SQLite)
    _db_url = SQLALCHEMY_DATABASE_URI
    if _db_url and 'mysql' in _db_url:
        _ssl_ca = os.path.join(BASE_DIR, 'isrgrootx1.pem')
        if os.path.exists(_ssl_ca):
            SQLALCHEMY_ENGINE_OPTIONS['connect_args'] = {
                'ssl': {'ca': _ssl_ca},
                'connect_timeout': 10
            }

    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB upload limit
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
    WTF_CSRF_ENABLED = True
