from flask_jwt_extended import get_jwt


def loja_atual_id():
    """ID da loja (tenant) do usuário autenticado — lido do JWT, nunca do
    corpo da requisição. Retorna None para super_admin (que não pertence a
    nenhuma loja)."""
    return get_jwt().get("loja_id")


def query_tenant(Model):
    """Query já filtrada pela loja do usuário autenticado. Use isto em vez
    de `Model.query` em toda rota tenant-scoped, para impedir que uma loja
    acesse/edite registros de outra (inclusive por ID direto na URL)."""
    return Model.query.filter_by(loja_id=loja_atual_id())
