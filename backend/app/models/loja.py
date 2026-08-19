from datetime import date, datetime, timezone

from app.extensions import db

PLANOS_VALIDOS = ("gratuito", "basico", "premium")
STATUS_VALIDOS = ("trial", "ativa", "suspensa", "cancelada")

# Limite de produtos cadastrados por plano. None = sem limite.
LIMITES_PLANO = {
    "gratuito": 100,
    "basico": 1000,
    "premium": None,
}


class Loja(db.Model):
    __tablename__ = "lojas"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    cnpj = db.Column(db.String(20), nullable=True)
    email_contato = db.Column(db.String(120), nullable=True)
    telefone = db.Column(db.String(20), nullable=True)
    endereco = db.Column(db.String(255), nullable=True)

    plano = db.Column(db.String(20), nullable=False, default="gratuito")
    status = db.Column(db.String(20), nullable=False, default="trial")
    trial_expira_em = db.Column(db.Date, nullable=True)
    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    lembrete_enviado_em = db.Column(db.Date, nullable=True)

    jwt_expiracao_horas = db.Column(db.Integer, nullable=False, default=12)
    senha_minima_caracteres = db.Column(db.Integer, nullable=False, default=6)

    # Configuração de emissão de nota fiscal (NF-e/NFC-e) — apenas estrutura
    # reservada para conectar um provedor terceiro (ex: Focus NFe, PlugNotas)
    # no futuro. Nada aqui se comunica com a SEFAZ; sem isso configurado, a
    # tela de Nota Fiscal só mostra instruções de como habilitar.
    nfe_provedor = db.Column(db.String(60), nullable=True)
    nfe_api_key = db.Column(db.String(255), nullable=True)
    nfe_ambiente = db.Column(db.String(12), nullable=False, default="homologacao")  # homologacao, producao
    nfe_cnpj_emitente = db.Column(db.String(20), nullable=True)

    def esta_ativa(self) -> bool:
        if self.status == "ativa":
            return True
        if self.status == "trial":
            return self.trial_expira_em is None or self.trial_expira_em >= date.today()
        return False

    def limite_produtos(self):
        return LIMITES_PLANO.get(self.plano)

    def to_dict_config_nfe(self) -> dict:
        chave_mascarada = None
        if self.nfe_api_key:
            chave_mascarada = f"{'*' * max(len(self.nfe_api_key) - 4, 0)}{self.nfe_api_key[-4:]}"
        return {
            "nfe_provedor": self.nfe_provedor,
            "nfe_api_key_configurada": bool(self.nfe_api_key),
            "nfe_api_key_mascarada": chave_mascarada,
            "nfe_ambiente": self.nfe_ambiente,
            "nfe_cnpj_emitente": self.nfe_cnpj_emitente,
        }

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nome": self.nome,
            "cnpj": self.cnpj,
            "email_contato": self.email_contato,
            "telefone": self.telefone,
            "endereco": self.endereco,
            "plano": self.plano,
            "status": self.status,
            "trial_expira_em": self.trial_expira_em.isoformat() if self.trial_expira_em else None,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
            "ativa": self.esta_ativa(),
            "limite_produtos": self.limite_produtos(),
            "jwt_expiracao_horas": self.jwt_expiracao_horas,
            "senha_minima_caracteres": self.senha_minima_caracteres,
        }
