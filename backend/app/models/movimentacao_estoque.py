from datetime import datetime, timezone

from app.extensions import db

TIPOS_VALIDOS = ("entrada", "saida", "ajuste")


class MovimentacaoEstoque(db.Model):
    __tablename__ = "movimentacoes_estoque"

    id = db.Column(db.Integer, primary_key=True)
    loja_id = db.Column(db.Integer, db.ForeignKey("lojas.id"), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey("produtos.id"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)

    tipo = db.Column(db.String(10), nullable=False)  # entrada, saida, ajuste
    quantidade = db.Column(db.Numeric(12, 3), nullable=False)
    motivo = db.Column(db.String(200), nullable=True)
    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    produto = db.relationship("Produto")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "produto_id": self.produto_id,
            "produto_nome": self.produto.nome if self.produto else None,
            "tipo": self.tipo,
            "quantidade": float(self.quantidade),
            "motivo": self.motivo,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
        }
