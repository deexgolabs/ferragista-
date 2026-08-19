from datetime import datetime, timezone

from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    loja_id = db.Column(db.Integer, db.ForeignKey("lojas.id"), nullable=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    perfil = db.Column(
        db.String(30), nullable=False, default="vendedor"
    )  # super_admin, admin, gerente, vendedor, estoquista
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    ultimo_login_em = db.Column(db.DateTime, nullable=True)
    percentual_comissao = db.Column(db.Numeric(5, 2), nullable=False, default=0)

    loja = db.relationship("Loja")

    def set_senha(self, senha: str) -> None:
        self.senha_hash = generate_password_hash(senha)

    def checar_senha(self, senha: str) -> bool:
        return check_password_hash(self.senha_hash, senha)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "loja_id": self.loja_id,
            "nome": self.nome,
            "email": self.email,
            "perfil": self.perfil,
            "ativo": self.ativo,
            "ultimo_login_em": self.ultimo_login_em.isoformat() if self.ultimo_login_em else None,
            "percentual_comissao": float(self.percentual_comissao),
        }
