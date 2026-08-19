from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models.produto import Produto
from app.models.movimentacao_estoque import MovimentacaoEstoque, TIPOS_VALIDOS
from app.services.estoque_service import registrar_movimentacao, EstoqueInsuficienteError
from app.utils.rbac import perfis_permitidos
from app.utils.tenant import query_tenant, loja_atual_id

estoque_bp = Blueprint("estoque", __name__)
_GESTAO = ("admin", "gerente", "estoquista")


@estoque_bp.get("/movimentacoes")
@jwt_required()
def listar_movimentacoes():
    query = query_tenant(MovimentacaoEstoque)
    if request.args.get("produto_id"):
        query = query.filter_by(produto_id=request.args.get("produto_id", type=int))
    movimentacoes = query.order_by(MovimentacaoEstoque.criado_em.desc()).limit(200).all()
    return jsonify([m.to_dict() for m in movimentacoes])


@estoque_bp.post("/movimentacoes")
@perfis_permitidos(*_GESTAO)
def criar_movimentacao():
    dados = request.get_json() or {}
    produto_id = dados.get("produto_id")
    tipo = dados.get("tipo")
    quantidade = dados.get("quantidade")

    if not produto_id or not tipo or quantidade is None:
        return jsonify({"erro": "produto_id, tipo e quantidade são obrigatórios"}), 400
    if tipo not in TIPOS_VALIDOS:
        return jsonify({"erro": f"tipo inválido. Use um de: {', '.join(TIPOS_VALIDOS)}"}), 400

    produto = query_tenant(Produto).filter_by(id=produto_id).first_or_404()

    try:
        movimentacao = registrar_movimentacao(
            loja_atual_id(), produto, tipo, quantidade, motivo=dados.get("motivo"), usuario_id=get_jwt_identity()
        )
    except EstoqueInsuficienteError as erro:
        return jsonify({"erro": str(erro)}), 400

    db.session.commit()
    return jsonify(movimentacao.to_dict()), 201
