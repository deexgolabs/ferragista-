from datetime import datetime, timezone

from app.extensions import db

STATUS_CAIXA_VALIDOS = ("aberto", "fechado")
TIPOS_MOVIMENTACAO_CAIXA_VALIDOS = ("suprimento", "sangria")


class CaixaSessao(db.Model):
    __tablename__ = "caixa_sessoes"

    id = db.Column(db.Integer, primary_key=True)
    loja_id = db.Column(db.Integer, db.ForeignKey("lojas.id"), nullable=False)
    usuario_abertura_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    usuario_fechamento_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)

    status = db.Column(db.String(10), nullable=False, default="aberto")
    valor_abertura = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    valor_fechamento_informado = db.Column(db.Numeric(10, 2), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)

    aberto_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    fechado_em = db.Column(db.DateTime, nullable=True)

    usuario_abertura = db.relationship("Usuario", foreign_keys=[usuario_abertura_id])
    usuario_fechamento = db.relationship("Usuario", foreign_keys=[usuario_fechamento_id])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "status": self.status,
            "valor_abertura": float(self.valor_abertura),
            "valor_fechamento_informado": float(self.valor_fechamento_informado) if self.valor_fechamento_informado is not None else None,
            "observacoes": self.observacoes,
            "usuario_abertura_nome": self.usuario_abertura.nome if self.usuario_abertura else None,
            "usuario_fechamento_nome": self.usuario_fechamento.nome if self.usuario_fechamento else None,
            "aberto_em": self.aberto_em.isoformat() if self.aberto_em else None,
            "fechado_em": self.fechado_em.isoformat() if self.fechado_em else None,
        }


class CaixaMovimentacao(db.Model):
    __tablename__ = "caixa_movimentacoes"

    id = db.Column(db.Integer, primary_key=True)
    loja_id = db.Column(db.Integer, db.ForeignKey("lojas.id"), nullable=False)
    caixa_sessao_id = db.Column(db.Integer, db.ForeignKey("caixa_sessoes.id"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)

    tipo = db.Column(db.String(12), nullable=False)  # suprimento, sangria
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    motivo = db.Column(db.String(200), nullable=True)
    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    usuario = db.relationship("Usuario")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tipo": self.tipo,
            "valor": float(self.valor),
            "motivo": self.motivo,
            "usuario_nome": self.usuario.nome if self.usuario else None,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
        }
