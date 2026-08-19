from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models.venda import Venda, VendaItem, FORMAS_PAGAMENTO_VALIDAS
from app.models.produto import Produto
from app.models.cliente import Cliente
from app.models.financeiro import Lancamento
from app.models.caixa import CaixaSessao
from app.services.estoque_service import registrar_movimentacao
from app.utils.rbac import perfis_permitidos
from app.utils.tenant import query_tenant, loja_atual_id

vendas_bp = Blueprint("vendas", __name__)
_PDV = ("admin", "gerente", "vendedor")


@vendas_bp.get("")
@perfis_permitidos(*_PDV)
def listar_vendas():
    query = query_tenant(Venda)
    if request.args.get("status"):
        query = query.filter_by(status=request.args.get("status"))
    vendas = query.order_by(Venda.criado_em.desc()).limit(200).all()
    return jsonify([v.to_dict() for v in vendas])


@vendas_bp.get("/<int:venda_id>")
@perfis_permitidos(*_PDV)
def obter_venda(venda_id):
    venda = query_tenant(Venda).filter_by(id=venda_id).first_or_404()
    return jsonify(venda.to_dict())


@vendas_bp.post("")
@perfis_permitidos(*_PDV)
def criar_venda():
    """Fecha uma venda do PDV: baixa o estoque de cada item e gera o
    lançamento financeiro correspondente (entrada já paga, ou conta a
    receber pendente se a forma de pagamento for fiado)."""
    dados = request.get_json() or {}
    itens = dados.get("itens") or []
    forma_pagamento = dados.get("forma_pagamento")

    if not itens:
        return jsonify({"erro": "informe ao menos um item"}), 400
    if forma_pagamento not in FORMAS_PAGAMENTO_VALIDAS:
        return jsonify({"erro": f"forma_pagamento inválida. Use uma de: {', '.join(FORMAS_PAGAMENTO_VALIDAS)}"}), 400

    loja_id = loja_atual_id()
    cliente = None
    if dados.get("cliente_id"):
        cliente = query_tenant(Cliente).filter_by(id=dados["cliente_id"]).first()
        if not cliente:
            return jsonify({"erro": "cliente não encontrado"}), 400

    if forma_pagamento == "fiado" and not cliente:
        return jsonify({"erro": "venda fiado exige um cliente vinculado"}), 400

    sessao_aberta = CaixaSessao.query.filter_by(loja_id=loja_id, status="aberto").first()

    venda = Venda(
        loja_id=loja_id,
        cliente_id=cliente.id if cliente else None,
        usuario_id=get_jwt_identity(),
        caixa_sessao_id=sessao_aberta.id if sessao_aberta else None,
        forma_pagamento=forma_pagamento,
        desconto=dados.get("desconto", 0),
    )
    db.session.add(venda)
    db.session.flush()

    for item in itens:
        produto = query_tenant(Produto).filter_by(id=item.get("produto_id")).first()
        if not produto:
            return jsonify({"erro": f"produto {item.get('produto_id')} não encontrado"}), 400
        quantidade = item.get("quantidade")
        if not quantidade or float(quantidade) <= 0:
            return jsonify({"erro": "quantidade deve ser maior que zero"}), 400
        if float(quantidade) > float(produto.quantidade_estoque):
            return jsonify({"erro": f"estoque insuficiente para {produto.nome}"}), 400

        db.session.add(
            VendaItem(
                venda_id=venda.id,
                produto_id=produto.id,
                quantidade=quantidade,
                preco_unitario=item.get("preco_unitario", produto.preco_venda),
            )
        )
        registrar_movimentacao(
            loja_id, produto, "saida", quantidade, motivo=f"venda #{venda.id}", usuario_id=get_jwt_identity()
        )

    total = venda.total()
    if forma_pagamento == "fiado":
        cliente.saldo_devedor = float(cliente.saldo_devedor) + total
        status_lancamento = "pendente"
    else:
        status_lancamento = "pago"

    lancamento = Lancamento(
        loja_id=loja_id,
        tipo="entrada",
        categoria="venda",
        descricao=f"Venda #{venda.id}" + (f" — {cliente.nome}" if cliente else ""),
        valor=total,
        status=status_lancamento,
        origem="venda",
        origem_id=venda.id,
    )
    db.session.add(lancamento)
    db.session.commit()
    return jsonify(venda.to_dict()), 201


@vendas_bp.put("/<int:venda_id>/cancelar")
@perfis_permitidos(*_PDV)
def cancelar_venda(venda_id):
    """Cancela a venda, estorna o estoque de cada item e ajusta o saldo
    devedor do cliente se a venda tiver sido fiado."""
    venda = query_tenant(Venda).filter_by(id=venda_id).first_or_404()
    if venda.status != "concluida":
        return jsonify({"erro": "apenas vendas concluídas podem ser canceladas"}), 400

    for item in venda.itens:
        registrar_movimentacao(
            venda.loja_id, item.produto, "entrada", item.quantidade,
            motivo=f"estorno venda #{venda.id}", usuario_id=get_jwt_identity(),
        )

    if venda.forma_pagamento == "fiado" and venda.cliente:
        venda.cliente.saldo_devedor = max(0.0, float(venda.cliente.saldo_devedor) - venda.total())

    lancamento = Lancamento.query.filter_by(origem="venda", origem_id=venda.id, loja_id=venda.loja_id).first()
    if lancamento:
        db.session.delete(lancamento)

    venda.status = "cancelada"
    db.session.commit()
    return jsonify(venda.to_dict())
