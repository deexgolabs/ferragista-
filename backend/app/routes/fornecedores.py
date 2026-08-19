from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models.fornecedor import Fornecedor
from app.utils.rbac import perfis_permitidos
from app.utils.tenant import query_tenant, loja_atual_id

fornecedores_bp = Blueprint("fornecedores", __name__)
_GESTAO = ("admin", "gerente", "estoquista")


@fornecedores_bp.get("")
@jwt_required()
def listar_fornecedores():
    busca = request.args.get("busca")
    query = query_tenant(Fornecedor)
    if busca:
        query = query.filter(Fornecedor.nome.ilike(f"%{busca}%"))
    fornecedores = query.order_by(Fornecedor.nome).all()
    return jsonify([f.to_dict() for f in fornecedores])


@fornecedores_bp.post("")
@perfis_permitidos(*_GESTAO)
def criar_fornecedor():
    dados = request.get_json() or {}
    if not dados.get("nome"):
        return jsonify({"erro": "nome é obrigatório"}), 400

    fornecedor = Fornecedor(
        loja_id=loja_atual_id(),
        nome=dados["nome"],
        cnpj=dados.get("cnpj"),
        telefone=dados.get("telefone"),
        email=dados.get("email"),
        endereco=dados.get("endereco"),
        contato=dados.get("contato"),
    )
    db.session.add(fornecedor)
    db.session.commit()
    return jsonify(fornecedor.to_dict()), 201


@fornecedores_bp.put("/<int:fornecedor_id>")
@perfis_permitidos(*_GESTAO)
def atualizar_fornecedor(fornecedor_id):
    fornecedor = query_tenant(Fornecedor).filter_by(id=fornecedor_id).first_or_404()
    dados = request.get_json() or {}
    for campo in ["nome", "cnpj", "telefone", "email", "endereco", "contato"]:
        if campo in dados:
            setattr(fornecedor, campo, dados[campo])
    db.session.commit()
    return jsonify(fornecedor.to_dict())


@fornecedores_bp.delete("/<int:fornecedor_id>")
@perfis_permitidos(*_GESTAO)
def excluir_fornecedor(fornecedor_id):
    fornecedor = query_tenant(Fornecedor).filter_by(id=fornecedor_id).first_or_404()
    db.session.delete(fornecedor)
    db.session.commit()
    return "", 204
