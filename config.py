import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'bbms-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'mysql+pymysql://3PLMHrkH8wePMwK.root:k7AZP0LCHBVyi3r5@gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/test'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {
            "ssl": {
                "ca": os.path.join(BASE_DIR, "isrgrootx1.pem")
            },
            "connect_timeout": 10
        },
        "pool_recycle": 60,
        "pool_pre_ping": True
    }
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB upload limit
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
    WTF_CSRF_ENABLED = True
