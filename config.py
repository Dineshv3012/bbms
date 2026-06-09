import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'bbms-secret-key-change-in-production')

    # Use DATABASE_URL if set (MySQL/TiDB in production).
    # Fall back to SQLite in /tmp — the only writable path on Vercel serverless.
    _db_url = os.environ.get('DATABASE_URL')
    # Fix common mistake: mysql:// must be mysql+pymysql:// for PyMySQL driver
    if _db_url and _db_url.startswith('mysql://'):
        _db_url = _db_url.replace('mysql://', 'mysql+pymysql://', 1)
    if _db_url:
        SQLALCHEMY_DATABASE_URI = _db_url
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/bbms_local.db'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.environ.get('SQLALCHEMY_ECHO', 'false').lower() == 'true'

    # Pool options only apply to MySQL/TiDB — not SQLite
    if _db_url and 'mysql' in (_db_url or ''):
        SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_recycle": 60,
            "pool_pre_ping": True,
        }
        _ssl_ca = os.path.join(BASE_DIR, 'isrgrootx1.pem')
        if os.path.exists(_ssl_ca):
            SQLALCHEMY_ENGINE_OPTIONS['connect_args'] = {
                'ssl': {'ca': _ssl_ca},
                'connect_timeout': 10
            }
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {}

    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB upload limit
    UPLOAD_FOLDER = os.path.join('/tmp', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
    WTF_CSRF_ENABLED = True
