from datetime import datetime, timezone

from app.extensions import db


class Cliente(db.Model):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)
    loja_id = db.Column(db.Integer, db.ForeignKey("lojas.id"), nullable=False)

    nome = db.Column(db.String(150), nullable=False)
    cpf_cnpj = db.Column(db.String(20), nullable=True)
    telefone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    endereco = db.Column(db.String(255), nullable=True)

    limite_fiado = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    saldo_devedor = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nome": self.nome,
            "cpf_cnpj": self.cpf_cnpj,
            "telefone": self.telefone,
            "email": self.email,
            "endereco": self.endereco,
            "limite_fiado": float(self.limite_fiado),
            "saldo_devedor": float(self.saldo_devedor),
        }
