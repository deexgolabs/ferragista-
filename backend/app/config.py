import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-key")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12)

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{(BASE_DIR / 'instance' / 'ferragista.db').as_posix()}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Rate limiting (Flask-Limiter). Em memória por padrão — se REDIS_URL
    # estiver configurado (ex: em produção com múltiplos processos), os
    # limites passam a ser compartilhados via Redis.
    RATELIMIT_STORAGE_URI = os.environ.get("REDIS_URL", "memory://")

    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5500")

    # E-mail (opcional). Sem MAIL_SERVER configurado, os e-mails são apenas
    # impressos no console — útil em desenvolvimento.
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "Ferragista+ <nao-responda@ferragista.local>")
