from datetime import datetime

from flask import Blueprint, request, jsonify
from sqlalchemy import func

from app.extensions import db
from app.models.loja import Loja, PLANOS_VALIDOS, STATUS_VALIDOS
from app.models.usuario import Usuario
from app.models.produto import Produto
from app.models.venda import Venda
from app.utils.rbac import perfis_permitidos

central_bp = Blueprint("central", __name__)


def _parse_data(valor):
    return datetime.strptime(valor, "%Y-%m-%d").date() if valor else None


@central_bp.get("/lojas")
@perfis_permitidos("super_admin")
def listar_lojas():
    contagem_produtos = dict(
        db.session.query(Produto.loja_id, func.count(Produto.id)).group_by(Produto.loja_id).all()
    )
    contagem_usuarios = dict(
        db.session.query(Usuario.loja_id, func.count(Usuario.id)).group_by(Usuario.loja_id).all()
    )

    lojas = Loja.query.order_by(Loja.criado_em.desc()).all()
    resultado = []
    for loja in lojas:
        item = loja.to_dict()
        item["total_produtos"] = contagem_produtos.get(loja.id, 0)
        item["total_usuarios"] = contagem_usuarios.get(loja.id, 0)
        resultado.append(item)

    return jsonify(resultado)


@central_bp.get("/lojas/<int:loja_id>")
@perfis_permitidos("super_admin")
def obter_loja(loja_id):
    loja = db.get_or_404(Loja, loja_id)
    return jsonify(loja.to_dict())


@central_bp.put("/lojas/<int:loja_id>")
@perfis_permitidos("super_admin")
def atualizar_loja(loja_id):
    loja = db.get_or_404(Loja, loja_id)
    dados = request.get_json() or {}

    if "status" in dados:
        if dados["status"] not in STATUS_VALIDOS:
            return jsonify({"erro": f"status inválido. Use um de: {', '.join(STATUS_VALIDOS)}"}), 400
        loja.status = dados["status"]
    if "plano" in dados:
        if dados["plano"] not in PLANOS_VALIDOS:
            return jsonify({"erro": f"plano inválido. Use um de: {', '.join(PLANOS_VALIDOS)}"}), 400
        loja.plano = dados["plano"]
    if "trial_expira_em" in dados:
        loja.trial_expira_em = _parse_data(dados["trial_expira_em"])
    if "nome" in dados:
        loja.nome = dados["nome"]
    if "telefone" in dados:
        loja.telefone = dados["telefone"]

    db.session.commit()
    return jsonify(loja.to_dict())


@central_bp.get("/metricas")
@perfis_permitidos("super_admin")
def metricas():
    total_lojas = Loja.query.count()
    por_status = dict(db.session.query(Loja.status, func.count(Loja.id)).group_by(Loja.status).all())
    return jsonify(
        {
            "total_lojas": total_lojas,
            "trial": por_status.get("trial", 0),
            "ativa": por_status.get("ativa", 0),
            "suspensa": por_status.get("suspensa", 0),
            "cancelada": por_status.get("cancelada", 0),
        }
    )


@central_bp.get("/crescimento")
@perfis_permitidos("super_admin")
def crescimento():
    lojas = Loja.query.filter(Loja.criado_em.isnot(None)).all()

    meses: dict[str, int] = {}
    for loja in lojas:
        chave = loja.criado_em.strftime("%Y-%m")
        meses[chave] = meses.get(chave, 0) + 1

    return jsonify(dict(sorted(meses.items())))


@central_bp.get("/analytics")
@perfis_permitidos("super_admin")
def analytics():
    contagem_vendas = dict(
        db.session.query(Venda.loja_id, func.count(Venda.id)).group_by(Venda.loja_id).all()
    )
    nomes_loja = {loja.id: loja.nome for loja in Loja.query.all()}

    ordenado = sorted(contagem_vendas.items(), key=lambda item: item[1], reverse=True)[:5]
    top_lojas = [{"loja_id": loja_id, "nome": nomes_loja.get(loja_id, "?"), "total": total} for loja_id, total in ordenado]

    return jsonify({"top_lojas_por_vendas": top_lojas})
