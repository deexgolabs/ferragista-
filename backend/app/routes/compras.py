from datetime import datetime, timezone

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models.compra import Compra, CompraItem, STATUS_COMPRA_VALIDOS
from app.models.produto import Produto
from app.models.financeiro import Lancamento
from app.services.estoque_service import registrar_movimentacao
from app.utils.rbac import perfis_permitidos
from app.utils.tenant import query_tenant, loja_atual_id

compras_bp = Blueprint("compras", __name__)
_GESTAO = ("admin", "gerente", "estoquista")


def _parse_data(valor):
    return datetime.strptime(valor, "%Y-%m-%d").date() if valor else None


@compras_bp.get("")
@perfis_permitidos(*_GESTAO)
def listar_compras():
    query = query_tenant(Compra)
    if request.args.get("status"):
        query = query.filter_by(status=request.args.get("status"))
    compras = query.order_by(Compra.data_pedido.desc()).all()
    return jsonify([c.to_dict() for c in compras])


@compras_bp.get("/<int:compra_id>")
@perfis_permitidos(*_GESTAO)
def obter_compra(compra_id):
    compra = query_tenant(Compra).filter_by(id=compra_id).first_or_404()
    return jsonify(compra.to_dict())


@compras_bp.post("")
@perfis_permitidos(*_GESTAO)
def criar_compra():
    dados = request.get_json() or {}
    itens = dados.get("itens") or []
    if not itens:
        return jsonify({"erro": "informe ao menos um item"}), 400

    loja_id = loja_atual_id()

    # Valida todos os itens antes de gravar qualquer coisa — evita um
    # cabeçalho de compra "órfão" (sem itens) se algum item no meio da
    # lista falhar a validação.
    itens_validados = []
    for item in itens:
        produto = query_tenant(Produto).filter_by(id=item.get("produto_id")).first()
        if not produto:
            return jsonify({"erro": f"produto {item.get('produto_id')} não encontrado"}), 400
        if not item.get("quantidade") or float(item["quantidade"]) <= 0:
            return jsonify({"erro": "quantidade deve ser maior que zero"}), 400
        preco_unitario = item.get("preco_unitario", produto.preco_custo or 0)
        if float(preco_unitario) < 0:
            return jsonify({"erro": f"preço unitário inválido para {produto.nome}"}), 400
        itens_validados.append((produto, item["quantidade"], preco_unitario))

    compra = Compra(loja_id=loja_id, fornecedor_id=dados.get("fornecedor_id"), observacoes=dados.get("observacoes"))
    db.session.add(compra)
    db.session.flush()

    for produto, quantidade, preco_unitario in itens_validados:
        db.session.add(
            CompraItem(
                compra_id=compra.id,
                produto_id=produto.id,
                quantidade=quantidade,
                preco_unitario=preco_unitario,
            )
        )

    db.session.commit()
    return jsonify(compra.to_dict()), 201


@compras_bp.put("/<int:compra_id>/receber")
@perfis_permitidos(*_GESTAO)
def receber_compra(compra_id):
    """Marca a compra como recebida: dá entrada no estoque de cada item e
    gera uma conta a pagar (lançamento financeiro pendente) no valor total."""
    from flask_jwt_extended import get_jwt_identity

    compra = query_tenant(Compra).filter_by(id=compra_id).first_or_404()
    if compra.status != "pendente":
        return jsonify({"erro": "apenas compras pendentes podem ser recebidas"}), 400

    for item in compra.itens:
        registrar_movimentacao(
            compra.loja_id,
            item.produto,
            "entrada",
            item.quantidade,
            motivo=f"compra #{compra.id}",
            usuario_id=get_jwt_identity(),
        )

    compra.status = "recebida"
    compra.data_recebimento = datetime.now(timezone.utc)

    dados = request.get_json() or {}
    lancamento = Lancamento(
        loja_id=compra.loja_id,
        tipo="saida",
        categoria="compra de mercadoria",
        descricao=f"Compra #{compra.id}" + (f" — {compra.fornecedor.nome}" if compra.fornecedor else ""),
        valor=compra.total(),
        status="pendente",
        vencimento=_parse_data(dados.get("vencimento")),
        origem="compra",
        origem_id=compra.id,
    )
    db.session.add(lancamento)
    db.session.commit()
    return jsonify(compra.to_dict())


@compras_bp.put("/<int:compra_id>/cancelar")
@perfis_permitidos(*_GESTAO)
def cancelar_compra(compra_id):
    compra = query_tenant(Compra).filter_by(id=compra_id).first_or_404()
    if compra.status != "pendente":
        return jsonify({"erro": "apenas compras pendentes podem ser canceladas"}), 400
    compra.status = "cancelada"
    db.session.commit()
    return jsonify(compra.to_dict())


@compras_bp.delete("/<int:compra_id>")
@perfis_permitidos(*_GESTAO)
def excluir_compra(compra_id):
    compra = query_tenant(Compra).filter_by(id=compra_id).first_or_404()
    if compra.status == "recebida":
        return jsonify({"erro": "não é possível excluir uma compra já recebida"}), 400
    db.session.delete(compra)
    db.session.commit()
    return "", 204
