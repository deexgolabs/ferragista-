def test_health(client):
    resposta = client.get("/api/health")
    assert resposta.status_code == 200
    assert resposta.get_json()["status"] == "ok"


def test_criar_loja_e_login(loja_admin):
    assert loja_admin["loja"]["status"] == "trial"
    assert loja_admin["usuario"]["perfil"] == "admin"
    assert "Authorization" in loja_admin["headers"]
