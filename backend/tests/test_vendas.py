def _criar_produto(client, headers, **overrides):
    dados = {"nome": "Parafuso 3/4", "codigo": "P001", "preco_custo": 0.10, "preco_venda": 0.25,
             "quantidade_estoque": 100, "estoque_minimo": 10}
    dados.update(overrides)
    return client.post("/api/produtos", headers=headers, json=dados).get_json()


def _criar_cliente(client, headers, **overrides):
    dados = {"nome": "Cliente Teste", "limite_fiado": 500}
    dados.update(overrides)
    return client.post("/api/clientes", headers=headers, json=dados).get_json()


class TestVendaAVista:
    def test_venda_dinheiro_baixa_estoque_e_gera_lancamento_pago(self, client, loja_admin):
        produto = _criar_produto(client, loja_admin["headers"])

        resposta = client.post(
            "/api/vendas",
            headers=loja_admin["headers"],
            json={"forma_pagamento": "dinheiro", "itens": [{"produto_id": produto["id"], "quantidade": 20}]},
        )
        assert resposta.status_code == 201
        venda = resposta.get_json()
        assert venda["total"] == 5.0
        assert venda["status"] == "concluida"

        produto_atualizado = client.get(f"/api/produtos/{produto['id']}", headers=loja_admin["headers"]).get_json()
        assert produto_atualizado["quantidade_estoque"] == 80

        lancamentos = client.get("/api/financeiro", headers=loja_admin["headers"]).get_json()
        assert len(lancamentos) == 1
        assert lancamentos[0]["tipo"] == "entrada"
        assert lancamentos[0]["status"] == "pago"
        assert lancamentos[0]["valor"] == 5.0

    def test_venda_aplica_desconto_no_total(self, client, loja_admin):
        produto = _criar_produto(client, loja_admin["headers"])

        resposta = client.post(
            "/api/vendas",
            headers=loja_admin["headers"],
            json={
                "forma_pagamento": "pix",
                "desconto": 1.0,
                "itens": [{"produto_id": produto["id"], "quantidade": 20}],
            },
        )
        venda = resposta.get_json()
        assert venda["subtotal"] == 5.0
        assert venda["total"] == 4.0

    def test_venda_com_desconto_negativo_e_rejeitada(self, client, loja_admin):
        produto = _criar_produto(client, loja_admin["headers"])
        resposta = client.post(
            "/api/vendas",
            headers=loja_admin["headers"],
            json={"forma_pagamento": "dinheiro", "desconto": -10, "itens": [{"produto_id": produto["id"], "quantidade": 1}]},
        )
        assert resposta.status_code == 400

    def test_venda_com_desconto_maior_que_subtotal_e_rejeitada(self, client, loja_admin):
        produto = _criar_produto(client, loja_admin["headers"])
        resposta = client.post(
            "/api/vendas",
            headers=loja_admin["headers"],
            json={
                "forma_pagamento": "dinheiro",
                "desconto": 999,
                "itens": [{"produto_id": produto["id"], "quantidade": 1}],
            },
        )
        assert resposta.status_code == 400

    def test_venda_com_preco_unitario_negativo_e_rejeitada(self, client, loja_admin):
        """Regressão: um vendedor não pode forjar um preço negativo pra
        derrubar o total da venda (ou até deixá-lo negativo)."""
        produto = _criar_produto(client, loja_admin["headers"], quantidade_estoque=100)
        resposta = client.post(
            "/api/vendas",
            headers=loja_admin["headers"],
            json={
                "forma_pagamento": "dinheiro",
                "itens": [{"produto_id": produto["id"], "quantidade": 1, "preco_unitario": -5}],
            },
        )
        assert resposta.status_code == 400

        # nada deve ter sido persistido: nem a venda, nem a baixa de estoque
        assert client.get("/api/vendas", headers=loja_admin["headers"]).get_json() == []
        produto_atual = client.get(f"/api/produtos/{produto['id']}", headers=loja_admin["headers"]).get_json()
        assert produto_atual["quantidade_estoque"] == 100

    def test_venda_com_quantidade_maior_que_estoque_e_rejeitada(self, client, loja_admin):
        produto = _criar_produto(client, loja_admin["headers"], quantidade_estoque=5)

        resposta = client.post(
            "/api/vendas",
            headers=loja_admin["headers"],
            json={"forma_pagamento": "dinheiro", "itens": [{"produto_id": produto["id"], "quantidade": 10}]},
        )
        assert resposta.status_code == 400

        inalterado = client.get(f"/api/produtos/{produto['id']}", headers=loja_admin["headers"]).get_json()
        assert inalterado["quantidade_estoque"] == 5  # nenhum item deve ter baixado

    def test_venda_sem_itens_e_rejeitada(self, client, loja_admin):
        resposta = client.post(
            "/api/vendas", headers=loja_admin["headers"], json={"forma_pagamento": "dinheiro", "itens": []}
        )
        assert resposta.status_code == 400


class TestVendaFiado:
    def test_venda_fiado_exige_cliente(self, client, loja_admin):
        produto = _criar_produto(client, loja_admin["headers"])
        resposta = client.post(
            "/api/vendas",
            headers=loja_admin["headers"],
            json={"forma_pagamento": "fiado", "itens": [{"produto_id": produto["id"], "quantidade": 5}]},
        )
        assert resposta.status_code == 400

    def test_venda_fiado_aumenta_saldo_devedor_e_gera_conta_a_receber(self, client, loja_admin):
        produto = _criar_produto(client, loja_admin["headers"])
        cliente = _criar_cliente(client, loja_admin["headers"])

        client.post(
            "/api/vendas",
            headers=loja_admin["headers"],
            json={
                "forma_pagamento": "fiado",
                "cliente_id": cliente["id"],
                "itens": [{"produto_id": produto["id"], "quantidade": 40}],
            },
        )

        cliente_atualizado = client.get("/api/clientes", headers=loja_admin["headers"]).get_json()[0]
        assert cliente_atualizado["saldo_devedor"] == 10.0

        lancamentos = client.get("/api/financeiro?status=pendente", headers=loja_admin["headers"]).get_json()
        assert len(lancamentos) == 1
        assert lancamentos[0]["tipo"] == "entrada"
        assert lancamentos[0]["status"] == "pendente"

    def test_quitar_conta_fiado_reduz_saldo_devedor_do_cliente(self, client, loja_admin):
        produto = _criar_produto(client, loja_admin["headers"])
        cliente = _criar_cliente(client, loja_admin["headers"])

        client.post(
            "/api/vendas",
            headers=loja_admin["headers"],
            json={
                "forma_pagamento": "fiado",
                "cliente_id": cliente["id"],
                "itens": [{"produto_id": produto["id"], "quantidade": 40}],
            },
        )
        lancamento = client.get("/api/financeiro?status=pendente", headers=loja_admin["headers"]).get_json()[0]

        resposta = client.put(f"/api/financeiro/{lancamento['id']}/quitar", headers=loja_admin["headers"])
        assert resposta.status_code == 200
        assert resposta.get_json()["status"] == "pago"

        cliente_atualizado = client.get("/api/clientes", headers=loja_admin["headers"]).get_json()[0]
        assert cliente_atualizado["saldo_devedor"] == 0.0


class TestCancelamentoVenda:
    def test_cancelar_venda_estorna_estoque_e_remove_lancamento(self, client, loja_admin):
        produto = _criar_produto(client, loja_admin["headers"])
        venda = client.post(
            "/api/vendas",
            headers=loja_admin["headers"],
            json={"forma_pagamento": "dinheiro", "itens": [{"produto_id": produto["id"], "quantidade": 30}]},
        ).get_json()

        resposta = client.put(f"/api/vendas/{venda['id']}/cancelar", headers=loja_admin["headers"])
        assert resposta.status_code == 200
        assert resposta.get_json()["status"] == "cancelada"

        produto_atualizado = client.get(f"/api/produtos/{produto['id']}", headers=loja_admin["headers"]).get_json()
        assert produto_atualizado["quantidade_estoque"] == 100  # voltou ao original

        lancamentos = client.get("/api/financeiro", headers=loja_admin["headers"]).get_json()
        assert lancamentos == []

    def test_cancelar_venda_fiado_reduz_saldo_devedor_do_cliente(self, client, loja_admin):
        produto = _criar_produto(client, loja_admin["headers"])
        cliente = _criar_cliente(client, loja_admin["headers"])

        venda = client.post(
            "/api/vendas",
            headers=loja_admin["headers"],
            json={
                "forma_pagamento": "fiado",
                "cliente_id": cliente["id"],
                "itens": [{"produto_id": produto["id"], "quantidade": 40}],
            },
        ).get_json()

        client.put(f"/api/vendas/{venda['id']}/cancelar", headers=loja_admin["headers"])

        cliente_atualizado = client.get("/api/clientes", headers=loja_admin["headers"]).get_json()[0]
        assert cliente_atualizado["saldo_devedor"] == 0.0

    def test_nao_pode_cancelar_venda_ja_cancelada(self, client, loja_admin):
        produto = _criar_produto(client, loja_admin["headers"])
        venda = client.post(
            "/api/vendas",
            headers=loja_admin["headers"],
            json={"forma_pagamento": "dinheiro", "itens": [{"produto_id": produto["id"], "quantidade": 5}]},
        ).get_json()

        client.put(f"/api/vendas/{venda['id']}/cancelar", headers=loja_admin["headers"])
        segunda_tentativa = client.put(f"/api/vendas/{venda['id']}/cancelar", headers=loja_admin["headers"])
        assert segunda_tentativa.status_code == 400

    def test_cancelar_venda_fiado_ja_quitada_nao_mexe_em_divida_de_outra_venda(self, client, loja_admin):
        """Regressão: cancelar uma venda fiado que já tinha sido paga não pode
        subtrair de novo do saldo_devedor — isso abateria (por engano) a
        dívida de uma venda fiado diferente e ainda pendente do mesmo cliente."""
        produto = _criar_produto(client, loja_admin["headers"], quantidade_estoque=1000)
        cliente = _criar_cliente(client, loja_admin["headers"])

        venda_paga = client.post(
            "/api/vendas",
            headers=loja_admin["headers"],
            json={
                "forma_pagamento": "fiado",
                "cliente_id": cliente["id"],
                "itens": [{"produto_id": produto["id"], "quantidade": 400, "preco_unitario": 0.25}],
            },
        ).get_json()
        lancamento_pago = client.get("/api/financeiro?status=pendente", headers=loja_admin["headers"]).get_json()[0]
        client.put(f"/api/financeiro/{lancamento_pago['id']}/quitar", headers=loja_admin["headers"])

        client.post(
            "/api/vendas",
            headers=loja_admin["headers"],
            json={
                "forma_pagamento": "fiado",
                "cliente_id": cliente["id"],
                "itens": [{"produto_id": produto["id"], "quantidade": 200, "preco_unitario": 0.25}],
            },
        )

        cliente_antes = client.get("/api/clientes", headers=loja_admin["headers"]).get_json()[0]
        assert cliente_antes["saldo_devedor"] == 50.0  # só a segunda venda, a primeira já foi paga

        client.put(f"/api/vendas/{venda_paga['id']}/cancelar", headers=loja_admin["headers"])

        cliente_depois = client.get("/api/clientes", headers=loja_admin["headers"]).get_json()[0]
        assert cliente_depois["saldo_devedor"] == 50.0  # não pode ter zerado a dívida da segunda venda


class TestCaixa:
    def test_abrir_e_ver_caixa_atual(self, client, loja_admin):
        resposta = client.post("/api/caixa/abrir", headers=loja_admin["headers"], json={"valor_abertura": 100})
        assert resposta.status_code == 201

        atual = client.get("/api/caixa/atual", headers=loja_admin["headers"]).get_json()
        assert atual["status"] == "aberto"
        assert atual["valor_abertura"] == 100.0

    def test_nao_pode_abrir_dois_caixas_ao_mesmo_tempo(self, client, loja_admin):
        client.post("/api/caixa/abrir", headers=loja_admin["headers"], json={"valor_abertura": 100})
        segunda_tentativa = client.post("/api/caixa/abrir", headers=loja_admin["headers"], json={"valor_abertura": 50})
        assert segunda_tentativa.status_code == 400

    def test_venda_se_vincula_ao_caixa_aberto_e_aparece_no_resumo(self, client, loja_admin):
        client.post("/api/caixa/abrir", headers=loja_admin["headers"], json={"valor_abertura": 100})
        produto = _criar_produto(client, loja_admin["headers"])
        client.post(
            "/api/vendas",
            headers=loja_admin["headers"],
            json={"forma_pagamento": "dinheiro", "itens": [{"produto_id": produto["id"], "quantidade": 20}]},
        )

        atual = client.get("/api/caixa/atual", headers=loja_admin["headers"]).get_json()
        assert atual["resumo"]["total_vendas"] == 5.0
        assert atual["resumo"]["vendas_por_forma_pagamento"]["dinheiro"] == 5.0

    def test_sangria_e_suprimento_afetam_valor_esperado_em_dinheiro(self, client, loja_admin):
        client.post("/api/caixa/abrir", headers=loja_admin["headers"], json={"valor_abertura": 100})
        produto = _criar_produto(client, loja_admin["headers"])
        client.post(
            "/api/vendas",
            headers=loja_admin["headers"],
            json={"forma_pagamento": "dinheiro", "itens": [{"produto_id": produto["id"], "quantidade": 20}]},
        )  # +5 em dinheiro

        client.post("/api/caixa/movimentacoes", headers=loja_admin["headers"], json={"tipo": "suprimento", "valor": 20})
        client.post("/api/caixa/movimentacoes", headers=loja_admin["headers"], json={"tipo": "sangria", "valor": 30})

        atual = client.get("/api/caixa/atual", headers=loja_admin["headers"]).get_json()
        # 100 (abertura) + 5 (venda dinheiro) + 20 (suprimento) - 30 (sangria) = 95
        assert atual["resumo"]["valor_esperado_dinheiro"] == 95.0

    def test_movimentacao_sem_caixa_aberto_e_rejeitada(self, client, loja_admin):
        resposta = client.post(
            "/api/caixa/movimentacoes", headers=loja_admin["headers"], json={"tipo": "sangria", "valor": 10}
        )
        assert resposta.status_code == 400

    def test_fechar_caixa_registra_valor_informado_e_libera_nova_abertura(self, client, loja_admin):
        client.post("/api/caixa/abrir", headers=loja_admin["headers"], json={"valor_abertura": 100})

        resposta = client.put(
            "/api/caixa/fechar",
            headers=loja_admin["headers"],
            json={"valor_fechamento_informado": 100, "observacoes": "confere"},
        )
        assert resposta.status_code == 200
        assert resposta.get_json()["status"] == "fechado"

        assert client.get("/api/caixa/atual", headers=loja_admin["headers"]).get_json() is None

        reabertura = client.post("/api/caixa/abrir", headers=loja_admin["headers"], json={"valor_abertura": 50})
        assert reabertura.status_code == 201
