import io

from app.models.loja import LIMITES_PLANO


def _criar_produto(client, headers, **overrides):
    dados = {"nome": "Parafuso 3/4", "codigo": "P001", "preco_custo": 0.10, "preco_venda": 0.25,
             "quantidade_estoque": 100, "estoque_minimo": 10}
    dados.update(overrides)
    return client.post("/api/produtos", headers=headers, json=dados)


def test_criar_e_listar_produto(client, loja_admin):
    resposta = _criar_produto(client, loja_admin["headers"])
    assert resposta.status_code == 201
    produto = resposta.get_json()
    assert produto["nome"] == "Parafuso 3/4"
    assert produto["estoque_baixo"] is False

    listagem = client.get("/api/produtos", headers=loja_admin["headers"])
    assert len(listagem.get_json()) == 1


def test_produto_sem_nome_e_rejeitado(client, loja_admin):
    resposta = client.post("/api/produtos", headers=loja_admin["headers"], json={"preco_venda": 10})
    assert resposta.status_code == 400


def test_produto_com_unidade_invalida_e_rejeitado(client, loja_admin):
    resposta = _criar_produto(client, loja_admin["headers"], unidade="tonelada")
    assert resposta.status_code == 400


def test_estoque_baixo_flag_atualiza_com_quantidade(client, loja_admin):
    criado = _criar_produto(client, loja_admin["headers"], quantidade_estoque=5, estoque_minimo=10).get_json()
    assert criado["estoque_baixo"] is True

    listagem_filtrada = client.get("/api/produtos?estoque_baixo=true", headers=loja_admin["headers"]).get_json()
    assert len(listagem_filtrada) == 1


def test_excluir_produto(client, loja_admin):
    criado = _criar_produto(client, loja_admin["headers"]).get_json()
    resposta = client.delete(f"/api/produtos/{criado['id']}", headers=loja_admin["headers"])
    assert resposta.status_code == 204

    listagem = client.get("/api/produtos", headers=loja_admin["headers"]).get_json()
    assert listagem == []


def test_limite_de_produtos_do_plano_gratuito_e_respeitado(client, loja_admin, monkeypatch):
    """Reduz o limite do plano gratuito pra 2 só neste teste, pra não
    precisar criar 100 produtos de verdade pra provar a regra de negócio."""
    monkeypatch.setitem(LIMITES_PLANO, "gratuito", 2)

    assert _criar_produto(client, loja_admin["headers"], codigo="P001").status_code == 201
    assert _criar_produto(client, loja_admin["headers"], codigo="P002").status_code == 201
    terceiro = _criar_produto(client, loja_admin["headers"], codigo="P003")
    assert terceiro.status_code == 402


class TestMovimentacoesEstoque:
    def test_entrada_soma_quantidade(self, client, loja_admin):
        produto = _criar_produto(client, loja_admin["headers"], quantidade_estoque=50).get_json()

        resposta = client.post(
            "/api/estoque/movimentacoes",
            headers=loja_admin["headers"],
            json={"produto_id": produto["id"], "tipo": "entrada", "quantidade": 20},
        )
        assert resposta.status_code == 201

        atualizado = client.get(f"/api/produtos/{produto['id']}", headers=loja_admin["headers"]).get_json()
        assert atualizado["quantidade_estoque"] == 70

    def test_saida_subtrai_quantidade(self, client, loja_admin):
        produto = _criar_produto(client, loja_admin["headers"], quantidade_estoque=50).get_json()

        client.post(
            "/api/estoque/movimentacoes",
            headers=loja_admin["headers"],
            json={"produto_id": produto["id"], "tipo": "saida", "quantidade": 15, "motivo": "quebra"},
        )

        atualizado = client.get(f"/api/produtos/{produto['id']}", headers=loja_admin["headers"]).get_json()
        assert atualizado["quantidade_estoque"] == 35

    def test_saida_maior_que_estoque_e_rejeitada(self, client, loja_admin):
        produto = _criar_produto(client, loja_admin["headers"], quantidade_estoque=10).get_json()

        resposta = client.post(
            "/api/estoque/movimentacoes",
            headers=loja_admin["headers"],
            json={"produto_id": produto["id"], "tipo": "saida", "quantidade": 999},
        )
        assert resposta.status_code == 400

        inalterado = client.get(f"/api/produtos/{produto['id']}", headers=loja_admin["headers"]).get_json()
        assert inalterado["quantidade_estoque"] == 10

    def test_ajuste_define_quantidade_exata(self, client, loja_admin):
        produto = _criar_produto(client, loja_admin["headers"], quantidade_estoque=999).get_json()

        client.post(
            "/api/estoque/movimentacoes",
            headers=loja_admin["headers"],
            json={"produto_id": produto["id"], "tipo": "ajuste", "quantidade": 42, "motivo": "inventário"},
        )

        atualizado = client.get(f"/api/produtos/{produto['id']}", headers=loja_admin["headers"]).get_json()
        assert atualizado["quantidade_estoque"] == 42


class TestImportacaoCsv:
    def test_importa_produtos_validos_e_cria_categoria(self, client, loja_admin):
        csv_conteudo = (
            "nome,codigo,categoria,unidade,preco_custo,preco_venda,quantidade_estoque,estoque_minimo\n"
            "Martelo,M001,Ferramentas,un,10.00,25.90,15,3\n"
            "Prego 18x27,PR18,Fixacao,kg,4.50,8.90,50,5\n"
        )
        dados_form = {"arquivo": (io.BytesIO(csv_conteudo.encode("utf-8")), "produtos.csv")}

        resposta = client.post(
            "/api/produtos/importar-csv",
            headers=loja_admin["headers"],
            data=dados_form,
            content_type="multipart/form-data",
        )
        assert resposta.status_code == 200
        resultado = resposta.get_json()
        assert resultado["criados"] == 2
        assert resultado["erros"] == []

        categorias = client.get("/api/produtos/categorias", headers=loja_admin["headers"]).get_json()
        assert {c["nome"] for c in categorias} == {"Ferramentas", "Fixacao"}

    def test_linha_sem_nome_e_reportada_como_erro_mas_nao_para_a_importacao(self, client, loja_admin):
        csv_conteudo = "nome,preco_venda\nMartelo,25.90\n,9.90\n"
        dados_form = {"arquivo": (io.BytesIO(csv_conteudo.encode("utf-8")), "produtos.csv")}

        resposta = client.post(
            "/api/produtos/importar-csv",
            headers=loja_admin["headers"],
            data=dados_form,
            content_type="multipart/form-data",
        )
        resultado = resposta.get_json()
        assert resultado["criados"] == 1
        assert len(resultado["erros"]) == 1

    def test_csv_sem_coluna_nome_e_rejeitado(self, client, loja_admin):
        csv_conteudo = "codigo,preco_venda\nP001,10\n"
        dados_form = {"arquivo": (io.BytesIO(csv_conteudo.encode("utf-8")), "produtos.csv")}

        resposta = client.post(
            "/api/produtos/importar-csv",
            headers=loja_admin["headers"],
            data=dados_form,
            content_type="multipart/form-data",
        )
        assert resposta.status_code == 400


class TestCodigoBarras:
    def test_gera_png_para_produto_com_codigo(self, client, loja_admin):
        produto = _criar_produto(client, loja_admin["headers"]).get_json()
        resposta = client.get(f"/api/produtos/{produto['id']}/codigo-barras.png", headers=loja_admin["headers"])
        assert resposta.status_code == 200
        assert resposta.content_type == "image/png"
        assert resposta.data[:8] == b"\x89PNG\r\n\x1a\n"  # assinatura de arquivo PNG

    def test_produto_sem_codigo_nao_gera_barras(self, client, loja_admin):
        produto = client.post(
            "/api/produtos", headers=loja_admin["headers"], json={"nome": "Sem código", "preco_venda": 5}
        ).get_json()

        resposta = client.get(f"/api/produtos/{produto['id']}/codigo-barras.png", headers=loja_admin["headers"])
        assert resposta.status_code == 400
