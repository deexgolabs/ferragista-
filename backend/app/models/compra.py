from datetime import datetime, timezone

from app.extensions import db

STATUS_COMPRA_VALIDOS = ("pendente", "recebida", "cancelada")


class Compra(db.Model):
    __tablename__ = "compras"

    id = db.Column(db.Integer, primary_key=True)
    loja_id = db.Column(db.Integer, db.ForeignKey("lojas.id"), nullable=False)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey("fornecedores.id"), nullable=True)

    status = db.Column(db.String(20), nullable=False, default="pendente")
    observacoes = db.Column(db.Text, nullable=True)
    data_pedido = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    data_recebimento = db.Column(db.DateTime, nullable=True)

    fornecedor = db.relationship("Fornecedor")
    itens = db.relationship("CompraItem", backref="compra", cascade="all, delete-orphan")

    def total(self) -> float:
        return round(sum(float(item.quantidade) * float(item.preco_unitario) for item in self.itens), 2)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "fornecedor_id": self.fornecedor_id,
            "fornecedor_nome": self.fornecedor.nome if self.fornecedor else None,
            "status": self.status,
            "observacoes": self.observacoes,
            "data_pedido": self.data_pedido.isoformat() if self.data_pedido else None,
            "data_recebimento": self.data_recebimento.isoformat() if self.data_recebimento else None,
            "total": self.total(),
            "itens": [item.to_dict() for item in self.itens],
        }


class CompraItem(db.Model):
    __tablename__ = "compra_itens"

    id = db.Column(db.Integer, primary_key=True)
    compra_id = db.Column(db.Integer, db.ForeignKey("compras.id"), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey("produtos.id"), nullable=False)
    quantidade = db.Column(db.Numeric(12, 3), nullable=False)
    preco_unitario = db.Column(db.Numeric(10, 2), nullable=False)

    produto = db.relationship("Produto")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "produto_id": self.produto_id,
            "produto_nome": self.produto.nome if self.produto else None,
            "quantidade": float(self.quantidade),
            "preco_unitario": float(self.preco_unitario),
            "subtotal": round(float(self.quantidade) * float(self.preco_unitario), 2),
        }
