from datetime import date, datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models.financeiro import Lancamento, TIPOS_VALIDOS, STATUS_VALIDOS
from app.utils.rbac import perfis_permitidos
from app.utils.tenant import query_tenant, loja_atual_id

financeiro_bp = Blueprint("financeiro", __name__)
_GESTAO = ("admin", "gerente")


def _parse_data(valor):
    return datetime.strptime(valor, "%Y-%m-%d").date() if valor else None


@financeiro_bp.get("")
@perfis_permitidos(*_GESTAO)
def listar_lancamentos():
    query = query_tenant(Lancamento)
    if request.args.get("tipo"):
        query = query.filter_by(tipo=request.args.get("tipo"))
    if request.args.get("status"):
        query = query.filter_by(status=request.args.get("status"))
    if request.args.get("data_inicio"):
        query = query.filter(Lancamento.data >= _parse_data(request.args.get("data_inicio")))
    if request.args.get("data_fim"):
        query = query.filter(Lancamento.data <= _parse_data(request.args.get("data_fim")))

    lancamentos = query.order_by(Lancamento.data.desc(), Lancamento.id.desc()).all()
    return jsonify([l.to_dict() for l in lancamentos])


@financeiro_bp.get("/resumo")
@perfis_permitidos(*_GESTAO)
def resumo():
    lancamentos = query_tenant(Lancamento).filter_by(status="pago").all()
    entradas = sum(float(l.valor) for l in lancamentos if l.tipo == "entrada")
    saidas = sum(float(l.valor) for l in lancamentos if l.tipo == "saida")

    pendentes = query_tenant(Lancamento).filter_by(status="pendente").all()
    a_receber = sum(float(l.valor) for l in pendentes if l.tipo == "entrada")
    a_pagar = sum(float(l.valor) for l in pendentes if l.tipo == "saida")

    return jsonify(
        {
            "entradas": round(entradas, 2),
            "saidas": round(saidas, 2),
            "saldo": round(entradas - saidas, 2),
            "a_receber": round(a_receber, 2),
            "a_pagar": round(a_pagar, 2),
        }
    )


@financeiro_bp.post("")
@perfis_permitidos(*_GESTAO)
def criar_lancamento():
    dados = request.get_json() or {}
    if dados.get("tipo") not in TIPOS_VALIDOS:
        return jsonify({"erro": f"tipo inválido. Use um de: {', '.join(TIPOS_VALIDOS)}"}), 400
    if not dados.get("valor"):
        return jsonify({"erro": "valor é obrigatório"}), 400

    status = dados.get("status", "pago")
    if status not in STATUS_VALIDOS:
        return jsonify({"erro": f"status inválido. Use um de: {', '.join(STATUS_VALIDOS)}"}), 400

    lancamento = Lancamento(
        loja_id=loja_atual_id(),
        tipo=dados["tipo"],
        categoria=dados.get("categoria", "outros"),
        descricao=dados.get("descricao"),
        valor=dados["valor"],
        status=status,
        data=_parse_data(dados.get("data")) or date.today(),
        vencimento=_parse_data(dados.get("vencimento")),
        pago_em=date.today() if status == "pago" else None,
    )
    db.session.add(lancamento)
    db.session.commit()
    return jsonify(lancamento.to_dict()), 201


@financeiro_bp.put("/<int:lancamento_id>")
@perfis_permitidos(*_GESTAO)
def atualizar_lancamento(lancamento_id):
    lancamento = query_tenant(Lancamento).filter_by(id=lancamento_id).first_or_404()
    dados = request.get_json() or {}

    for campo in ["categoria", "descricao", "valor"]:
        if campo in dados:
            setattr(lancamento, campo, dados[campo])
    if "data" in dados:
        lancamento.data = _parse_data(dados["data"])
    if "vencimento" in dados:
        lancamento.vencimento = _parse_data(dados["vencimento"])

    db.session.commit()
    return jsonify(lancamento.to_dict())


@financeiro_bp.put("/<int:lancamento_id>/quitar")
@perfis_permitidos(*_GESTAO)
def quitar_lancamento(lancamento_id):
    lancamento = query_tenant(Lancamento).filter_by(id=lancamento_id).first_or_404()
    if lancamento.status == "pago":
        return jsonify({"erro": "lançamento já está pago"}), 400

    lancamento.status = "pago"
    lancamento.pago_em = date.today()

    if lancamento.origem == "venda" and lancamento.origem_id:
        from app.models.venda import Venda
        venda = db.session.get(Venda, lancamento.origem_id)
        if venda and venda.cliente:
            venda.cliente.saldo_devedor = max(0.0, float(venda.cliente.saldo_devedor) - float(lancamento.valor))

    db.session.commit()
    return jsonify(lancamento.to_dict())


@financeiro_bp.delete("/<int:lancamento_id>")
@perfis_permitidos(*_GESTAO)
def excluir_lancamento(lancamento_id):
    lancamento = query_tenant(Lancamento).filter_by(id=lancamento_id).first_or_404()
    if lancamento.origem != "manual":
        return jsonify({"erro": "apenas lançamentos manuais podem ser excluídos diretamente"}), 400
    db.session.delete(lancamento)
    db.session.commit()
    return "", 204
