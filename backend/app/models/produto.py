from datetime import datetime, timezone

from app.extensions import db

UNIDADES_VALIDAS = ("un", "kg", "g", "m", "cm", "L", "ml", "cx", "pct", "par", "rolo")


class Produto(db.Model):
    __tablename__ = "produtos"

    id = db.Column(db.Integer, primary_key=True)
    loja_id = db.Column(db.Integer, db.ForeignKey("lojas.id"), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey("categorias.id"), nullable=True)

    nome = db.Column(db.String(150), nullable=False)
    codigo = db.Column(db.String(60), nullable=True)  # SKU / código de barras
    unidade = db.Column(db.String(10), nullable=False, default="un")
    preco_custo = db.Column(db.Numeric(10, 2), nullable=True)
    preco_venda = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    quantidade_estoque = db.Column(db.Numeric(12, 3), nullable=False, default=0)
    estoque_minimo = db.Column(db.Numeric(12, 3), nullable=False, default=0)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    categoria = db.relationship("Categoria")

    def estoque_baixo(self) -> bool:
        return float(self.quantidade_estoque) <= float(self.estoque_minimo)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nome": self.nome,
            "codigo": self.codigo,
            "categoria_id": self.categoria_id,
            "categoria_nome": self.categoria.nome if self.categoria else None,
            "unidade": self.unidade,
            "preco_custo": float(self.preco_custo) if self.preco_custo is not None else None,
            "preco_venda": float(self.preco_venda),
            "quantidade_estoque": float(self.quantidade_estoque),
            "estoque_minimo": float(self.estoque_minimo),
            "estoque_baixo": self.estoque_baixo(),
            "ativo": self.ativo,
        }
