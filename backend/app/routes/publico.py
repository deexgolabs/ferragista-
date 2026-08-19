from datetime import date, timedelta

from flask import Blueprint, current_app, request, jsonify
from flask_jwt_extended import create_access_token

from app.extensions import db, limiter
from app.models.loja import Loja
from app.models.usuario import Usuario
from app.utils.email import enviar_email

publico_bp = Blueprint("publico", __name__)

DIAS_TRIAL = 14


@publico_bp.post("/cadastrar-loja")
@limiter.limit("5 per hour")
def cadastrar_loja():
    """Cadastro público (self-service) de uma nova loja. Cria a loja em modo
    trial e o primeiro usuário (admin) vinculado a ela, já retornando um
    token de acesso (login automático)."""
    dados = request.get_json() or {}
    nome_loja = dados.get("nome_loja")
    nome_responsavel = dados.get("nome_responsavel")
    email = dados.get("email")
    senha = dados.get("senha")

    if not all([nome_loja, nome_responsavel, email, senha]):
        return jsonify(
            {"erro": "nome_loja, nome_responsavel, email e senha são obrigatórios"}
        ), 400

    if Usuario.query.filter_by(email=email).first():
        return jsonify({"erro": "e-mail já cadastrado"}), 409

    loja = Loja(
        nome=nome_loja,
        email_contato=email,
        plano="gratuito",
        status="trial",
        trial_expira_em=date.today() + timedelta(days=DIAS_TRIAL),
    )
    db.session.add(loja)
    db.session.flush()  # garante loja.id antes de criar o usuário

    usuario = Usuario(nome=nome_responsavel, email=email, perfil="admin", loja_id=loja.id)
    usuario.set_senha(senha)
    db.session.add(usuario)
    db.session.commit()

    link_app = f"{current_app.config['FRONTEND_URL']}/pages/login.html"
    enviar_email(
        email,
        "Bem-vindo(a) ao Ferragista+!",
        f"Olá, {nome_responsavel}!\n\n"
        f"A conta da {nome_loja} foi criada com sucesso e já está liberada por {DIAS_TRIAL} dias "
        f"em modo de teste, sem custo.\n\nAcesse quando quiser em: {link_app}\n\n"
        f"Qualquer dúvida, é só responder este e-mail.",
    )

    token = create_access_token(
        identity=str(usuario.id),
        additional_claims={"perfil": usuario.perfil, "loja_id": usuario.loja_id},
    )
    return jsonify({"access_token": token, "usuario": usuario.to_dict(), "loja": loja.to_dict()}), 201
