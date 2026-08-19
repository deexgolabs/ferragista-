from datetime import datetime, timezone

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models.caixa import CaixaSessao, CaixaMovimentacao, TIPOS_MOVIMENTACAO_CAIXA_VALIDOS
from app.models.venda import Venda
from app.utils.rbac import perfis_permitidos
from app.utils.tenant import query_tenant, loja_atual_id

caixa_bp = Blueprint("caixa", __name__)
_PDV = ("admin", "gerente", "vendedor")


def _sessao_aberta(loja_id):
    return CaixaSessao.query.filter_by(loja_id=loja_id, status="aberto").first()


def _resumo_sessao(sessao: CaixaSessao) -> dict:
    vendas = Venda.query.filter_by(caixa_sessao_id=sessao.id, status="concluida").all()
    por_forma: dict[str, float] = {}
    for venda in vendas:
        por_forma[venda.forma_pagamento] = por_forma.get(venda.forma_pagamento, 0.0) + venda.total()

    movimentacoes = CaixaMovimentacao.query.filter_by(caixa_sessao_id=sessao.id).all()
    suprimentos = sum(float(m.valor) for m in movimentacoes if m.tipo == "suprimento")
    sangrias = sum(float(m.valor) for m in movimentacoes if m.tipo == "sangria")

    vendas_dinheiro = por_forma.get("dinheiro", 0.0)
    valor_esperado_dinheiro = float(sessao.valor_abertura) + vendas_dinheiro + suprimentos - sangrias

    return {
        "vendas_por_forma_pagamento": por_forma,
        "total_vendas": round(sum(por_forma.values()), 2),
        "quantidade_vendas": len(vendas),
        "suprimentos": round(suprimentos, 2),
        "sangrias": round(sangrias, 2),
        "valor_esperado_dinheiro": round(valor_esperado_dinheiro, 2),
    }


@caixa_bp.get("/atual")
@perfis_permitidos(*_PDV)
def caixa_atual():
    sessao = _sessao_aberta(loja_atual_id())
    if not sessao:
        return jsonify(None)
    dados = sessao.to_dict()
    dados["resumo"] = _resumo_sessao(sessao)
    return jsonify(dados)


@caixa_bp.get("/sessoes")
@perfis_permitidos(*_PDV)
def listar_sessoes():
    sessoes = query_tenant(CaixaSessao).order_by(CaixaSessao.aberto_em.desc()).limit(50).all()
    return jsonify([s.to_dict() for s in sessoes])


@caixa_bp.get("/sessoes/<int:sessao_id>")
@perfis_permitidos(*_PDV)
def obter_sessao(sessao_id):
    sessao = query_tenant(CaixaSessao).filter_by(id=sessao_id).first_or_404()
    dados = sessao.to_dict()
    dados["resumo"] = _resumo_sessao(sessao)
    return jsonify(dados)


@caixa_bp.post("/abrir")
@perfis_permitidos(*_PDV)
def abrir_caixa():
    loja_id = loja_atual_id()
    if _sessao_aberta(loja_id):
        return jsonify({"erro": "já existe um caixa aberto"}), 400

    dados = request.get_json() or {}
    sessao = CaixaSessao(
        loja_id=loja_id,
        usuario_abertura_id=get_jwt_identity(),
        valor_abertura=dados.get("valor_abertura", 0),
    )
    db.session.add(sessao)
    db.session.commit()
    return jsonify(sessao.to_dict()), 201


@caixa_bp.put("/fechar")
@perfis_permitidos(*_PDV)
def fechar_caixa():
    sessao = _sessao_aberta(loja_atual_id())
    if not sessao:
        return jsonify({"erro": "não há caixa aberto"}), 400

    dados = request.get_json() or {}
    sessao.status = "fechado"
    sessao.valor_fechamento_informado = dados.get("valor_fechamento_informado")
    sessao.observacoes = dados.get("observacoes")
    sessao.usuario_fechamento_id = get_jwt_identity()
    sessao.fechado_em = datetime.now(timezone.utc)
    db.session.commit()

    resultado = sessao.to_dict()
    resultado["resumo"] = _resumo_sessao(sessao)
    return jsonify(resultado)


@caixa_bp.get("/movimentacoes")
@perfis_permitidos(*_PDV)
def listar_movimentacoes():
    sessao = _sessao_aberta(loja_atual_id())
    if not sessao:
        return jsonify([])
    movimentacoes = (
        CaixaMovimentacao.query.filter_by(caixa_sessao_id=sessao.id).order_by(CaixaMovimentacao.criado_em.desc()).all()
    )
    return jsonify([m.to_dict() for m in movimentacoes])


@caixa_bp.post("/movimentacoes")
@perfis_permitidos(*_PDV)
def criar_movimentacao():
    loja_id = loja_atual_id()
    sessao = _sessao_aberta(loja_id)
    if not sessao:
        return jsonify({"erro": "abra o caixa antes de registrar sangria/suprimento"}), 400

    dados = request.get_json() or {}
    tipo = dados.get("tipo")
    valor = dados.get("valor")
    if tipo not in TIPOS_MOVIMENTACAO_CAIXA_VALIDOS:
        return jsonify({"erro": f"tipo inválido. Use um de: {', '.join(TIPOS_MOVIMENTACAO_CAIXA_VALIDOS)}"}), 400
    if not valor or float(valor) <= 0:
        return jsonify({"erro": "valor deve ser maior que zero"}), 400

    movimentacao = CaixaMovimentacao(
        loja_id=loja_id,
        caixa_sessao_id=sessao.id,
        usuario_id=get_jwt_identity(),
        tipo=tipo,
        valor=valor,
        motivo=dados.get("motivo"),
    )
    db.session.add(movimentacao)
    db.session.commit()
    return jsonify(movimentacao.to_dict()), 201
