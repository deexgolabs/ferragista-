import secrets
from datetime import datetime, timedelta, timezone

from app.extensions import db

VALIDADE_MINUTOS = 60


class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    usado = db.Column(db.Boolean, default=False)

    @staticmethod
    def gerar(usuario_id: int) -> "PasswordResetToken":
        return PasswordResetToken(usuario_id=usuario_id, token=secrets.token_urlsafe(32))

    def valido(self) -> bool:
        if self.usado:
            return False
        criado_em = self.criado_em
        if criado_em.tzinfo is None:
            criado_em = criado_em.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) - criado_em <= timedelta(minutes=VALIDADE_MINUTOS)
