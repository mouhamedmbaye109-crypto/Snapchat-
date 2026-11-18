import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-change-me")
    DATABASE_URL = os.environ.get("DATABASE_URL", "")
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
    PUBLIC_URL = os.environ.get("PUBLIC_URL", "http://127.0.0.1:8000")
    CODE_ACCES = os.environ.get("CODE_ACCES", "SNAPPLUS2026")
    MAX_CONTENT_LENGTH = 64 * 1024


class ProdConfig(Config):
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PREFERRED_URL_SCHEME = "https"

    def __init__(self):
        if self.SECRET_KEY == "dev-insecure-change-me":
            raise RuntimeError("SECRET_KEY manquant")
        if len(self.ADMIN_TOKEN) < 24:
            raise RuntimeError("ADMIN_TOKEN manquant ou trop court (24 caracteres)")
        if not self.DATABASE_URL:
            raise RuntimeError("DATABASE_URL manquant")