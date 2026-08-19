def _criar_produto(client, headers, **overrides):
    dados = {"nome": "Parafuso 3/4", "codigo": "P001", "preco_custo": 0.10, "preco_venda": 0.25,
             "quantidade_estoque": 10, "estoque_minimo": 10}
    dados.update(overrides)
    return client.post("/api/produtos", headers=headers, json=dados).get_json()


def _criar_fornecedor(client, headers, **overrides):
    dados = {"nome": "Fornecedor Teste"}
    dados.update(overrides)
    return client.post("/api/fornecedores", headers=headers, json=dados).get_json()


class TestCompras:
    def test_criar_compra_nao_altera_estoque_ainda(self, client, loja_admin):
        produto = _criar_produto(client, loja_admin["headers"], quantidade_estoque=10)
        fornecedor = _criar_fornecedor(client, loja_admin["headers"])

        resposta = client.post(
            "/api/compras",
            headers=loja_admin["headers"],
            json={
                "fornecedor_id": fornecedor["id"],
                "itens": [{"produto_id": produto["id"], "quantidade": 50, "preco_unitario": 0.10}],
            },
        )
        assert resposta.status_code == 201
        compra = resposta.get_json()
        assert compra["status"] == "pendente"
        assert compra["total"] == 5.0

        produto_inalterado = client.get(f"/api/produtos/{produto['id']}", headers=loja_admin["headers"]).get_json()
        assert produto_inalterado["quantidade_estoque"] == 10

    def test_receber_compra_da_entrada_no_estoque_e_gera_conta_a_pagar(self, client, loja_admin):
        produto = _criar_produto(client, loja_admin["headers"], quantidade_estoque=10)
        compra = client.post(
            "/api/compras",
            headers=loja_admin["headers"],
            json={"itens": [{"produto_id": produto["id"], "quantidade": 50, "preco_unitario": 0.10}]},
        ).get_json()

        resposta = client.put(f"/api/compras/{compra['id']}/receber", headers=loja_admin["headers"], json={})
        assert resposta.status_code == 200
        assert resposta.get_json()["status"] == "recebida"

        produto_atualizado = client.get(f"/api/produtos/{produto['id']}", headers=loja_admin["headers"]).get_json()
        assert produto_atualizado["quantidade_estoque"] == 60

        contas_a_pagar = client.get("/api/financeiro?tipo=saida", headers=loja_admin["headers"]).get_json()
        assert len(contas_a_pagar) == 1
        assert contas_a_pagar[0]["status"] == "pendente"
        assert contas_a_pagar[0]["valor"] == 5.0

    def test_nao_pode_receber_compra_ja_recebida(self, client, loja_admin):
        produto = _criar_produto(client, loja_admin["headers"])
        compra = client.post(
            "/api/compras",
            headers=loja_admin["headers"],
            json={"itens": [{"produto_id": produto["id"], "quantidade": 10, "preco_unitario": 0.10}]},
        ).get_json()

        client.put(f"/api/compras/{compra['id']}/receber", headers=loja_admin["headers"], json={})
        segunda_tentativa = client.put(f"/api/compras/{compra['id']}/receber", headers=loja_admin["headers"], json={})
        assert segunda_tentativa.status_code == 400

    def test_cancelar_compra_pendente(self, client, loja_admin):
        produto = _criar_produto(client, loja_admin["headers"])
        compra = client.post(
            "/api/compras",
            headers=loja_admin["headers"],
            json={"itens": [{"produto_id": produto["id"], "quantidade": 10, "preco_unitario": 0.10}]},
        ).get_json()

        resposta = client.put(f"/api/compras/{compra['id']}/cancelar", headers=loja_admin["headers"])
        assert resposta.status_code == 200
        assert resposta.get_json()["status"] == "cancelada"

    def test_compra_com_preco_unitario_negativo_e_rejeitada(self, client, loja_admin):
        """Regressão: preço unitário negativo deixaria compra.total() negativo,
        inflando o saldo/lucro do dashboard quando a conta a pagar fosse gerada."""
        produto = _criar_produto(client, loja_admin["headers"])
        resposta = client.post(
            "/api/compras",
            headers=loja_admin["headers"],
            json={"itens": [{"produto_id": produto["id"], "quantidade": 10, "preco_unitario": -0.10}]},
        )
        assert resposta.status_code == 400


class TestFinanceiro:
    def test_criar_lancamento_manual_pago(self, client, loja_admin):
        resposta = client.post(
            "/api/financeiro",
            headers=loja_admin["headers"],
            json={"tipo": "saida", "categoria": "aluguel", "valor": 1200, "status": "pago"},
        )
        assert resposta.status_code == 201

        resumo = client.get("/api/financeiro/resumo", headers=loja_admin["headers"]).get_json()
        assert resumo["saidas"] == 1200.0
        assert resumo["saldo"] == -1200.0

    def test_quitar_lancamento_pendente(self, client, loja_admin):
        criado = client.post(
            "/api/financeiro",
            headers=loja_admin["headers"],
            json={"tipo": "saida", "categoria": "aluguel", "valor": 500, "status": "pendente", "vencimento": "2026-01-01"},
        ).get_json()

        resposta = client.put(f"/api/financeiro/{criado['id']}/quitar", headers=loja_admin["headers"])
        assert resposta.status_code == 200
        assert resposta.get_json()["status"] == "pago"

        segunda_tentativa = client.put(f"/api/financeiro/{criado['id']}/quitar", headers=loja_admin["headers"])
        assert segunda_tentativa.status_code == 400

    def test_criar_lancamento_com_valor_negativo_e_rejeitado(self, client, loja_admin):
        """Regressão: `not dados.get("valor")` só rejeitava zero — um valor
        negativo passava direto e virava soma em vez de subtração no resumo."""
        resposta = client.post(
            "/api/financeiro",
            headers=loja_admin["headers"],
            json={"tipo": "saida", "categoria": "aluguel", "valor": -500},
        )
        assert resposta.status_code == 400

    def test_nao_pode_editar_lancamento_de_origem_venda(self, client, loja_admin):
        """Regressão: editar o valor de um lançamento gerado por uma venda o
        dessincroniza do total real da venda, e pode incluir quitação errada."""
        produto = _criar_produto(client, loja_admin["headers"])
        client.post(
            "/api/vendas",
            headers=loja_admin["headers"],
            json={"forma_pagamento": "dinheiro", "itens": [{"produto_id": produto["id"], "quantidade": 5}]},
        )
        lancamento = client.get("/api/financeiro", headers=loja_admin["headers"]).get_json()[0]

        resposta = client.put(
            f"/api/financeiro/{lancamento['id']}", headers=loja_admin["headers"], json={"valor": 1}
        )
        assert resposta.status_code == 400

    def test_editar_lancamento_manual_com_valor_negativo_e_rejeitado(self, client, loja_admin):
        criado = client.post(
            "/api/financeiro",
            headers=loja_admin["headers"],
            json={"tipo": "saida", "categoria": "aluguel", "valor": 500},
        ).get_json()

        resposta = client.put(
            f"/api/financeiro/{criado['id']}", headers=loja_admin["headers"], json={"valor": -1}
        )
        assert resposta.status_code == 400

    def test_nao_pode_excluir_lancamento_de_origem_venda(self, client, loja_admin):
        produto = _criar_produto(client, loja_admin["headers"])
        client.post(
            "/api/vendas",
            headers=loja_admin["headers"],
            json={"forma_pagamento": "dinheiro", "itens": [{"produto_id": produto["id"], "quantidade": 5}]},
        )
        lancamento = client.get("/api/financeiro", headers=loja_admin["headers"]).get_json()[0]

        resposta = client.delete(f"/api/financeiro/{lancamento['id']}", headers=loja_admin["headers"])
        assert resposta.status_code == 400


class TestRelatorios:
    def test_curva_abc_com_produto_unico_classifica_como_a(self, client, loja_admin):
        """Regressão do bug encontrado manualmente: um único produto vendido
        soma 100% do faturamento e cruza o corte de 80%/95% imediatamente —
        mas continua sendo, na prática, o produto mais importante da loja, e
        precisa ficar na classe A, não cair em C por "estourar" o corte."""
        produto = _criar_produto(client, loja_admin["headers"])
        client.post(
            "/api/vendas",
            headers=loja_admin["headers"],
            json={"forma_pagamento": "dinheiro", "itens": [{"produto_id": produto["id"], "quantidade": 5}]},
        )

        curva = client.get("/api/relatorios/curva-abc", headers=loja_admin["headers"]).get_json()
        assert len(curva) == 1
        assert curva[0]["classe"] == "A"

    def test_curva_abc_classifica_produto_de_cauda_longa_como_c(self, client, loja_admin):
        produto_principal = _criar_produto(client, loja_admin["headers"], codigo="P001", preco_venda=100, quantidade_estoque=10)
        produto_pequeno = _criar_produto(client, loja_admin["headers"], codigo="P002", preco_venda=1, quantidade_estoque=10)

        client.post(
            "/api/vendas",
            headers=loja_admin["headers"],
            json={"forma_pagamento": "dinheiro", "itens": [{"produto_id": produto_principal["id"], "quantidade": 1}]},
        )
        client.post(
            "/api/vendas",
            headers=loja_admin["headers"],
            json={"forma_pagamento": "dinheiro", "itens": [{"produto_id": produto_pequeno["id"], "quantidade": 1}]},
        )

        curva = client.get("/api/relatorios/curva-abc", headers=loja_admin["headers"]).get_json()
        por_produto = {item["produto_id"]: item["classe"] for item in curva}
        assert por_produto[produto_principal["id"]] == "A"
        assert por_produto[produto_pequeno["id"]] == "C"

    def test_margem_calcula_lucro_correto(self, client, loja_admin):
        produto = _criar_produto(client, loja_admin["headers"], preco_custo=0.10, preco_venda=0.25, quantidade_estoque=100)
        client.post(
            "/api/vendas",
            headers=loja_admin["headers"],
            json={"forma_pagamento": "dinheiro", "itens": [{"produto_id": produto["id"], "quantidade": 20}]},
        )

        margem = client.get("/api/relatorios/margem", headers=loja_admin["headers"]).get_json()
        assert margem["receita_total"] == 5.0
        assert margem["custo_total"] == 2.0
        assert margem["margem_total"] == 3.0

    def test_comissao_calcula_valor_devido_ao_vendedor(self, client, loja_admin):
        produto = _criar_produto(client, loja_admin["headers"], preco_venda=1.0, quantidade_estoque=100)

        usuario_id = loja_admin["usuario"]["id"]
        client.put(
            f"/api/auth/usuarios/{usuario_id}",
            headers=loja_admin["headers"],
            json={"percentual_comissao": 10},
        )

        client.post(
            "/api/vendas",
            headers=loja_admin["headers"],
            json={"forma_pagamento": "dinheiro", "itens": [{"produto_id": produto["id"], "quantidade": 50}]},
        )

        comissoes = client.get("/api/relatorios/comissoes", headers=loja_admin["headers"]).get_json()
        assert len(comissoes) == 1
        assert comissoes[0]["total_vendido"] == 50.0
        assert comissoes[0]["comissao_devida"] == 5.0

    def test_dashboard_agrega_vendas_e_estoque_baixo(self, client, loja_admin):
        _criar_produto(client, loja_admin["headers"], quantidade_estoque=2, estoque_minimo=10)
        dashboard = client.get("/api/relatorios/dashboard", headers=loja_admin["headers"]).get_json()
        assert dashboard["produtos_estoque_baixo"] == 1
        assert dashboard["total_produtos_ativos"] == 1

    def test_notificacoes_lista_estoque_baixo_e_conta_vencendo(self, client, loja_admin):
        _criar_produto(client, loja_admin["headers"], quantidade_estoque=1, estoque_minimo=10)
        client.post(
            "/api/financeiro",
            headers=loja_admin["headers"],
            json={"tipo": "saida", "categoria": "aluguel", "valor": 500, "status": "pendente", "vencimento": "2026-01-01"},
        )

        notificacoes = client.get("/api/relatorios/notificacoes", headers=loja_admin["headers"]).get_json()
        tipos = {n["tipo"] for n in notificacoes}
        assert "estoque_baixo" in tipos
        assert "conta_vencendo" in tipos
