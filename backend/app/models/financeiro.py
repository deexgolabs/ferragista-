from datetime import date, datetime, timezone

from app.extensions import db

TIPOS_VALIDOS = ("entrada", "saida")
STATUS_VALIDOS = ("pago", "pendente")
ORIGENS_VALIDAS = ("manual", "venda", "compra")


class Lancamento(db.Model):
    __tablename__ = "lancamentos"

    id = db.Column(db.Integer, primary_key=True)
    loja_id = db.Column(db.Integer, db.ForeignKey("lojas.id"), nullable=False)

    tipo = db.Column(db.String(10), nullable=False)  # entrada, saida
    categoria = db.Column(db.String(60), nullable=False, default="outros")
    descricao = db.Column(db.String(200), nullable=True)
    valor = db.Column(db.Numeric(10, 2), nullable=False)

    status = db.Column(db.String(10), nullable=False, default="pago")  # pago, pendente
    data = db.Column(db.Date, nullable=False, default=date.today)
    vencimento = db.Column(db.Date, nullable=True)
    pago_em = db.Column(db.Date, nullable=True)

    origem = db.Column(db.String(10), nullable=False, default="manual")  # manual, venda, compra
    origem_id = db.Column(db.Integer, nullable=True)

    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tipo": self.tipo,
            "categoria": self.categoria,
            "descricao": self.descricao,
            "valor": float(self.valor),
            "status": self.status,
            "data": self.data.isoformat() if self.data else None,
            "vencimento": self.vencimento.isoformat() if self.vencimento else None,
            "pago_em": self.pago_em.isoformat() if self.pago_em else None,
            "origem": self.origem,
            "origem_id": self.origem_id,
        }
