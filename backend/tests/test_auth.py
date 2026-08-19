from tests.conftest import autenticar


def test_login_com_senha_errada_falha(client, loja_admin):
    resposta = client.post("/api/auth/login", json={"email": loja_admin["email"], "senha": "senha-errada"})
    assert resposta.status_code == 401


def test_login_com_email_inexistente_falha(client):
    resposta = client.post("/api/auth/login", json={"email": "ninguem@teste.com", "senha": "qualquer"})
    assert resposta.status_code == 401


def test_cadastro_com_email_duplicado_falha(client, loja_admin):
    resposta = client.post(
        "/api/publico/cadastrar-loja",
        json={
            "nome_loja": "Outra loja",
            "nome_responsavel": "Outro admin",
            "email": loja_admin["email"],
            "senha": "senha123",
        },
    )
    assert resposta.status_code == 409


def test_usuario_ve_seus_proprios_dados_em_me(client, loja_admin):
    resposta = client.get("/api/auth/me", headers=loja_admin["headers"])
    assert resposta.status_code == 200
    assert resposta.get_json()["email"] == loja_admin["email"]


def test_perfil_vendedor_nao_pode_criar_produto(client, loja_admin):
    """`perfis_permitidos` deve bloquear perfis fora da lista autorizada —
    aqui, vendedor tentando uma ação restrita a admin/gerente/estoquista."""
    resposta = client.post(
        "/api/auth/registrar",
        headers=loja_admin["headers"],
        json={"nome": "Vendedor Teste", "email": "vendedor@teste.com", "senha": "senha123", "perfil": "vendedor"},
    )
    assert resposta.status_code == 201
    headers_vendedor = autenticar(client, "vendedor@teste.com", "senha123")

    resposta = client.post(
        "/api/produtos",
        headers=headers_vendedor,
        json={"nome": "Produto qualquer", "preco_venda": 10},
    )
    assert resposta.status_code == 403


def test_senha_curta_no_registro_e_rejeitada(client, loja_admin):
    resposta = client.post(
        "/api/auth/registrar",
        headers=loja_admin["headers"],
        json={"nome": "Fulano", "email": "fulano@teste.com", "senha": "123", "perfil": "vendedor"},
    )
    assert resposta.status_code == 400


class TestIsolamentoMultiTenant:
    """A garantia mais crítica do sistema: uma loja nunca pode ler, editar
    ou excluir dados de outra loja, mesmo sabendo o ID exato do registro."""

    def test_loja_b_nao_ve_produto_da_loja_a_por_id_direto(self, client, criar_loja):
        loja_a = criar_loja(nome_loja="Loja A", email="admin.a@teste.com")
        loja_b = criar_loja(nome_loja="Loja B", email="admin.b@teste.com")

        criado = client.post(
            "/api/produtos", headers=loja_a["headers"], json={"nome": "Produto da loja A", "preco_venda": 10}
        )
        produto_id = criado.get_json()["id"]

        resposta = client.get(f"/api/produtos/{produto_id}", headers=loja_b["headers"])
        assert resposta.status_code == 404

    def test_loja_b_nao_consegue_editar_produto_da_loja_a(self, client, criar_loja):
        loja_a = criar_loja(nome_loja="Loja A", email="admin.a2@teste.com")
        loja_b = criar_loja(nome_loja="Loja B", email="admin.b2@teste.com")

        criado = client.post(
            "/api/produtos", headers=loja_a["headers"], json={"nome": "Produto da loja A", "preco_venda": 10}
        )
        produto_id = criado.get_json()["id"]

        resposta = client.put(
            f"/api/produtos/{produto_id}", headers=loja_b["headers"], json={"nome": "Hackeado"}
        )
        assert resposta.status_code == 404

        # confirma que o produto da loja A não foi alterado
        confirmacao = client.get(f"/api/produtos/{produto_id}", headers=loja_a["headers"])
        assert confirmacao.get_json()["nome"] == "Produto da loja A"

    def test_listagem_de_produtos_nao_vaza_entre_lojas(self, client, criar_loja):
        loja_a = criar_loja(nome_loja="Loja A", email="admin.a3@teste.com")
        loja_b = criar_loja(nome_loja="Loja B", email="admin.b3@teste.com")

        client.post("/api/produtos", headers=loja_a["headers"], json={"nome": "Só da A", "preco_venda": 10})
        client.post("/api/produtos", headers=loja_b["headers"], json={"nome": "Só da B", "preco_venda": 10})

        produtos_a = client.get("/api/produtos", headers=loja_a["headers"]).get_json()
        produtos_b = client.get("/api/produtos", headers=loja_b["headers"]).get_json()

        assert [p["nome"] for p in produtos_a] == ["Só da A"]
        assert [p["nome"] for p in produtos_b] == ["Só da B"]

    def test_usuario_da_loja_a_nao_aparece_na_listagem_da_loja_b(self, client, criar_loja):
        loja_a = criar_loja(nome_loja="Loja A", email="admin.a4@teste.com")
        loja_b = criar_loja(nome_loja="Loja B", email="admin.b4@teste.com")

        usuarios_b = client.get("/api/auth/usuarios", headers=loja_b["headers"]).get_json()
        emails_b = [u["email"] for u in usuarios_b]

        assert loja_a["email"] not in emails_b
        assert loja_b["email"] in emails_b
