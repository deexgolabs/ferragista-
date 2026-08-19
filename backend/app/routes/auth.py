from datetime import datetime, timedelta, timezone

from flask import Blueprint, current_app, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from app.extensions import db, limiter
from app.models.usuario import Usuario
from app.models.loja import Loja
from app.models.password_reset import PasswordResetToken
from app.utils.rbac import perfis_permitidos
from app.utils.tenant import query_tenant, loja_atual_id
from app.utils.email import enviar_email

auth_bp = Blueprint("auth", __name__)

PERFIS_VALIDOS = ("admin", "gerente", "vendedor", "estoquista")


def _validar_politica_senha(senha: str, loja_id) -> str | None:
    minimo = 6
    if loja_id:
        loja = db.session.get(Loja, loja_id)
        if loja:
            minimo = loja.senha_minima_caracteres
    if len(senha or "") < minimo:
        return f"a senha deve ter pelo menos {minimo} caracteres"
    return None


@auth_bp.post("/registrar")
@perfis_permitidos("admin")
def registrar():
    """Cadastro de novos usuários do sistema — restrito ao admin da própria
    loja. O loja_id nunca vem do corpo da requisição."""
    dados = request.get_json() or {}
    nome = dados.get("nome")
    email = dados.get("email")
    senha = dados.get("senha")
    perfil = dados.get("perfil", "vendedor")

    if not nome or not email or not senha:
        return jsonify({"erro": "nome, email e senha são obrigatórios"}), 400

    if perfil not in PERFIS_VALIDOS:
        return jsonify({"erro": f"perfil inválido. Use um de: {', '.join(PERFIS_VALIDOS)}"}), 400

    erro_senha = _validar_politica_senha(senha, loja_atual_id())
    if erro_senha:
        return jsonify({"erro": erro_senha}), 400

    if Usuario.query.filter_by(email=email).first():
        return jsonify({"erro": "e-mail já cadastrado"}), 409

    usuario = Usuario(nome=nome, email=email, perfil=perfil, loja_id=loja_atual_id())
    usuario.set_senha(senha)
    db.session.add(usuario)
    db.session.commit()

    return jsonify(usuario.to_dict()), 201


@auth_bp.get("/usuarios")
@perfis_permitidos("admin")
def listar_usuarios():
    usuarios = query_tenant(Usuario).order_by(Usuario.nome).all()
    return jsonify([u.to_dict() for u in usuarios])


@auth_bp.put("/usuarios/<int:usuario_id>")
@perfis_permitidos("admin")
def atualizar_usuario(usuario_id):
    usuario = query_tenant(Usuario).filter_by(id=usuario_id).first_or_404()
    dados = request.get_json() or {}

    if "perfil" in dados:
        if dados["perfil"] not in PERFIS_VALIDOS:
            return jsonify({"erro": f"perfil inválido. Use um de: {', '.join(PERFIS_VALIDOS)}"}), 400
        usuario.perfil = dados["perfil"]
    if "ativo" in dados:
        usuario.ativo = bool(dados["ativo"])
    if "nome" in dados:
        usuario.nome = dados["nome"]
    if "percentual_comissao" in dados:
        usuario.percentual_comissao = dados["percentual_comissao"]

    db.session.commit()
    return jsonify(usuario.to_dict())


@auth_bp.delete("/usuarios/<int:usuario_id>")
@perfis_permitidos("admin")
def excluir_usuario(usuario_id):
    usuario = query_tenant(Usuario).filter_by(id=usuario_id).first_or_404()
    if usuario.id == int(get_jwt_identity()):
        return jsonify({"erro": "você não pode excluir seu próprio usuário"}), 400
    db.session.delete(usuario)
    db.session.commit()
    return "", 204


@auth_bp.post("/login")
@limiter.limit("5 per minute")
def login():
    dados = request.get_json() or {}
    email = dados.get("email")
    senha = dados.get("senha")

    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario or not usuario.checar_senha(senha or ""):
        return jsonify({"erro": "credenciais inválidas"}), 401

    if not usuario.ativo:
        return jsonify({"erro": "usuário inativo"}), 403

    if usuario.loja_id is not None:
        if not usuario.loja or not usuario.loja.esta_ativa():
            return jsonify(
                {"erro": "assinatura da loja suspensa ou expirada. Contate o suporte."}
            ), 403

    expiracao = None
    if usuario.loja_id is not None and usuario.loja:
        expiracao = timedelta(hours=usuario.loja.jwt_expiracao_horas)

    token = create_access_token(
        identity=str(usuario.id),
        additional_claims={"perfil": usuario.perfil, "loja_id": usuario.loja_id},
        expires_delta=expiracao,
    )

    usuario.ultimo_login_em = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({"access_token": token, "usuario": usuario.to_dict()})


@auth_bp.get("/me")
@jwt_required()
def me():
    usuario = db.get_or_404(Usuario, get_jwt_identity())
    return jsonify(usuario.to_dict())


@auth_bp.put("/me")
@jwt_required()
def atualizar_meu_perfil():
    usuario = db.get_or_404(Usuario, get_jwt_identity())
    dados = request.get_json() or {}

    if "nome" in dados and dados["nome"]:
        usuario.nome = dados["nome"]
    if "email" in dados and dados["email"] and dados["email"] != usuario.email:
        if Usuario.query.filter_by(email=dados["email"]).first():
            return jsonify({"erro": "e-mail já cadastrado"}), 409
        usuario.email = dados["email"]

    db.session.commit()
    return jsonify(usuario.to_dict())


@auth_bp.post("/trocar-senha")
@jwt_required()
def trocar_senha():
    usuario = db.get_or_404(Usuario, get_jwt_identity())
    dados = request.get_json() or {}
    senha_atual = dados.get("senha_atual")
    nova_senha = dados.get("nova_senha")

    if not senha_atual or not nova_senha:
        return jsonify({"erro": "senha_atual e nova_senha são obrigatórios"}), 400

    if not usuario.checar_senha(senha_atual):
        return jsonify({"erro": "senha atual incorreta"}), 401

    erro_senha = _validar_politica_senha(nova_senha, usuario.loja_id)
    if erro_senha:
        return jsonify({"erro": erro_senha}), 400

    usuario.set_senha(nova_senha)
    db.session.commit()
    return jsonify({"mensagem": "Senha alterada com sucesso."})


@auth_bp.post("/esqueci-senha")
@limiter.limit("5 per minute")
def esqueci_senha():
    dados = request.get_json() or {}
    email = dados.get("email")
    usuario = Usuario.query.filter_by(email=email).first()

    if usuario:
        reset_token = PasswordResetToken.gerar(usuario.id)
        db.session.add(reset_token)
        db.session.commit()

        link = f"{current_app.config['FRONTEND_URL']}/pages/redefinir-senha.html?token={reset_token.token}"
        enviar_email(
            usuario.email,
            "Redefinição de senha — Ferragista+",
            f"Olá, {usuario.nome}!\n\nClique no link abaixo para redefinir sua senha "
            f"(válido por 60 minutos):\n{link}\n\nSe você não solicitou, ignore este e-mail.",
        )

    return jsonify({"mensagem": "Se o e-mail existir em nossa base, um link de redefinição foi enviado."})


@auth_bp.post("/redefinir-senha")
def redefinir_senha():
    dados = request.get_json() or {}
    token_valor = dados.get("token")
    nova_senha = dados.get("nova_senha")

    if not token_valor or not nova_senha:
        return jsonify({"erro": "token e nova_senha são obrigatórios"}), 400

    reset_token = PasswordResetToken.query.filter_by(token=token_valor).first()
    if not reset_token or not reset_token.valido():
        return jsonify({"erro": "token inválido ou expirado"}), 400

    usuario = db.get_or_404(Usuario, reset_token.usuario_id)

    erro_senha = _validar_politica_senha(nova_senha, usuario.loja_id)
    if erro_senha:
        return jsonify({"erro": erro_senha}), 400

    usuario.set_senha(nova_senha)
    reset_token.usado = True
    db.session.commit()

    return jsonify({"mensagem": "Senha redefinida com sucesso."})
