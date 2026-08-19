from app.extensions import db
from app.models.movimentacao_estoque import MovimentacaoEstoque


def registrar_movimentacao(loja_id, produto, tipo, quantidade, motivo=None, usuario_id=None):
    """Aplica uma movimentação de estoque no produto (ajustando a quantidade
    atual) e registra o histórico. `quantidade` é sempre positiva; o sentido
    (soma ou subtrai) é decidido pelo `tipo`. Não faz commit — quem chamar
    decide quando persistir, para poder agrupar com outras alterações na
    mesma transação (ex: itens de uma venda)."""
    quantidade = abs(float(quantidade))

    if tipo == "entrada":
        produto.quantidade_estoque = float(produto.quantidade_estoque) + quantidade
    elif tipo == "saida":
        produto.quantidade_estoque = float(produto.quantidade_estoque) - quantidade
    elif tipo == "ajuste":
        produto.quantidade_estoque = quantidade
    else:
        raise ValueError(f"tipo de movimentação inválido: {tipo}")

    movimentacao = MovimentacaoEstoque(
        loja_id=loja_id,
        produto_id=produto.id,
        usuario_id=usuario_id,
        tipo=tipo,
        quantidade=quantidade,
        motivo=motivo,
    )
    db.session.add(movimentacao)
    return movimentacao
