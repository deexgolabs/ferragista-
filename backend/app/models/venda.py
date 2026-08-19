from datetime import datetime, timezone

from app.extensions import db

FORMAS_PAGAMENTO_VALIDAS = ("dinheiro", "pix", "cartao_debito", "cartao_credito", "fiado")
STATUS_VENDA_VALIDOS = ("concluida", "cancelada")


class Venda(db.Model):
    __tablename__ = "vendas"

    id = db.Column(db.Integer, primary_key=True)
    loja_id = db.Column(db.Integer, db.ForeignKey("lojas.id"), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    caixa_sessao_id = db.Column(db.Integer, db.ForeignKey("caixa_sessoes.id"), nullable=True)

    forma_pagamento = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="concluida")
    desconto = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    cliente = db.relationship("Cliente")
    usuario = db.relationship("Usuario")
    itens = db.relationship("VendaItem", backref="venda", cascade="all, delete-orphan")

    def subtotal(self) -> float:
        return round(sum(float(item.quantidade) * float(item.preco_unitario) for item in self.itens), 2)

    def total(self) -> float:
        return round(self.subtotal() - float(self.desconto), 2)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "cliente_id": self.cliente_id,
            "cliente_nome": self.cliente.nome if self.cliente else None,
            "usuario_id": self.usuario_id,
            "usuario_nome": self.usuario.nome if self.usuario else None,
            "forma_pagamento": self.forma_pagamento,
            "status": self.status,
            "desconto": float(self.desconto),
            "subtotal": self.subtotal(),
            "total": self.total(),
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
            "itens": [item.to_dict() for item in self.itens],
        }


class VendaItem(db.Model):
    __tablename__ = "venda_itens"

    id = db.Column(db.Integer, primary_key=True)
    venda_id = db.Column(db.Integer, db.ForeignKey("vendas.id"), nullable=False)
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
