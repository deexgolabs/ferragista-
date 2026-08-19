from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models.cliente import Cliente
from app.utils.rbac import perfis_permitidos
from app.utils.tenant import query_tenant, loja_atual_id

clientes_bp = Blueprint("clientes", __name__)
_GESTAO = ("admin", "gerente", "vendedor")


@clientes_bp.get("")
@jwt_required()
def listar_clientes():
    busca = request.args.get("busca")
    query = query_tenant(Cliente)
    if busca:
        query = query.filter(Cliente.nome.ilike(f"%{busca}%"))
    clientes = query.order_by(Cliente.nome).all()
    return jsonify([c.to_dict() for c in clientes])


@clientes_bp.get("/<int:cliente_id>")
@jwt_required()
def obter_cliente(cliente_id):
    cliente = query_tenant(Cliente).filter_by(id=cliente_id).first_or_404()
    return jsonify(cliente.to_dict())


@clientes_bp.post("")
@perfis_permitidos(*_GESTAO)
def criar_cliente():
    dados = request.get_json() or {}
    if not dados.get("nome"):
        return jsonify({"erro": "nome é obrigatório"}), 400

    cliente = Cliente(
        loja_id=loja_atual_id(),
        nome=dados["nome"],
        cpf_cnpj=dados.get("cpf_cnpj"),
        telefone=dados.get("telefone"),
        email=dados.get("email"),
        endereco=dados.get("endereco"),
        limite_fiado=dados.get("limite_fiado", 0),
    )
    db.session.add(cliente)
    db.session.commit()
    return jsonify(cliente.to_dict()), 201


@clientes_bp.put("/<int:cliente_id>")
@perfis_permitidos(*_GESTAO)
def atualizar_cliente(cliente_id):
    cliente = query_tenant(Cliente).filter_by(id=cliente_id).first_or_404()
    dados = request.get_json() or {}
    for campo in ["nome", "cpf_cnpj", "telefone", "email", "endereco", "limite_fiado"]:
        if campo in dados:
            setattr(cliente, campo, dados[campo])
    db.session.commit()
    return jsonify(cliente.to_dict())


@clientes_bp.delete("/<int:cliente_id>")
@perfis_permitidos(*_GESTAO)
def excluir_cliente(cliente_id):
    cliente = query_tenant(Cliente).filter_by(id=cliente_id).first_or_404()
    db.session.delete(cliente)
    db.session.commit()
    return "", 204
