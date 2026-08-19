from flask import Blueprint, request, jsonify

from app.extensions import db
from app.models.loja import Loja
from app.utils.rbac import perfis_permitidos
from app.utils.tenant import loja_atual_id

loja_config_bp = Blueprint("loja_config", __name__)

PROVEDORES_NFE_VALIDOS = ("focus_nfe", "plugnotas", "enotas", "outro")
AMBIENTES_NFE_VALIDOS = ("homologacao", "producao")


@loja_config_bp.get("/config-nfe")
@perfis_permitidos("admin", "gerente")
def obter_config_nfe():
    loja = db.get_or_404(Loja, loja_atual_id())
    return jsonify(loja.to_dict_config_nfe())


@loja_config_bp.put("/config-nfe")
@perfis_permitidos("admin")
def atualizar_config_nfe():
    """Apenas grava a configuração (provedor, chave de API, ambiente,
    CNPJ emitente) — não emite nenhuma nota fiscal de verdade. A emissão
    real depende de contratar um provedor (Focus NFe, PlugNotas, eNotas) ou
    implementar a comunicação direta com a SEFAZ usando um certificado
    digital, o que exige credenciais que só o dono da loja possui."""
    loja = db.get_or_404(Loja, loja_atual_id())
    dados = request.get_json() or {}

    if "nfe_provedor" in dados:
        if dados["nfe_provedor"] and dados["nfe_provedor"] not in PROVEDORES_NFE_VALIDOS:
            return jsonify({"erro": f"provedor inválido. Use um de: {', '.join(PROVEDORES_NFE_VALIDOS)}"}), 400
        loja.nfe_provedor = dados["nfe_provedor"] or None
    if "nfe_api_key" in dados and dados["nfe_api_key"]:
        loja.nfe_api_key = dados["nfe_api_key"]
    if "nfe_ambiente" in dados:
        if dados["nfe_ambiente"] not in AMBIENTES_NFE_VALIDOS:
            return jsonify({"erro": f"ambiente inválido. Use um de: {', '.join(AMBIENTES_NFE_VALIDOS)}"}), 400
        loja.nfe_ambiente = dados["nfe_ambiente"]
    if "nfe_cnpj_emitente" in dados:
        loja.nfe_cnpj_emitente = dados["nfe_cnpj_emitente"] or None

    db.session.commit()
    return jsonify(loja.to_dict_config_nfe())
