import pytest

from app import create_app
from app.config import Config
from app.extensions import db as _db


@pytest.fixture()
def app(tmp_path):
    db_path = tmp_path / "test.db"

    class TestConfig(Config):
        TESTING = True
        RATELIMIT_ENABLED = False
        SECRET_KEY = "test-secret-key-with-at-least-32-bytes-long"
        JWT_SECRET_KEY = "test-jwt-secret-key-with-at-least-32-bytes-long"
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"
        MAIL_SERVER = None  # e-mails só impressos no console durante os testes

    flask_app = create_app(TestConfig)

    with flask_app.app_context():
        _db.create_all()
        yield flask_app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def criar_loja(client):
    """Fábrica: cadastra uma loja + usuário admin via endpoint público e
    devolve headers de autenticação prontos, além dos dados da loja/usuário.
    Chame várias vezes no mesmo teste para simular lojas diferentes
    (essencial pros testes de isolamento multi-tenant)."""

    contador = {"valor": 0}

    def _criar(nome_loja="Ferragem Teste", email=None, senha="senha123"):
        contador["valor"] += 1
        email = email or f"admin{contador['valor']}@teste.com"

        resposta = client.post(
            "/api/publico/cadastrar-loja",
            json={
                "nome_loja": nome_loja,
                "nome_responsavel": "Admin Teste",
                "email": email,
                "senha": senha,
            },
        )
        assert resposta.status_code == 201, resposta.get_json()
        dados = resposta.get_json()
        return {
            "headers": {"Authorization": f"Bearer {dados['access_token']}"},
            "token": dados["access_token"],
            "usuario": dados["usuario"],
            "loja": dados["loja"],
            "email": email,
            "senha": senha,
        }

    return _criar


@pytest.fixture()
def loja_admin(criar_loja):
    """Uma única loja + admin já autenticado — o caso comum da maioria dos testes."""
    return criar_loja()


def autenticar(client, email, senha):
    resposta = client.post("/api/auth/login", json={"email": email, "senha": senha})
    assert resposta.status_code == 200, resposta.get_json()
    token = resposta.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
