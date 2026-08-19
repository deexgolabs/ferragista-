from sqlalchemy import update

from app.extensions import db
from app.models.movimentacao_estoque import MovimentacaoEstoque
from app.models.produto import Produto


class EstoqueInsuficienteError(ValueError):
    pass


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
        # UPDATE atômico condicionado ao estoque atual (em vez de checar em
        # Python e só depois escrever) — evita que duas vendas concorrentes
        # do último item, lidas antes de qualquer uma commitar, passem pela
        # checagem e derrubem o estoque para negativo.
        resultado = db.session.execute(
            update(Produto)
            .where(Produto.id == produto.id, Produto.quantidade_estoque >= quantidade)
            .values(quantidade_estoque=Produto.quantidade_estoque - quantidade)
            # Sem isso, o SQLAlchemy tenta recalcular o novo valor em Python
            # pra sincronizar o objeto em memória, e mistura Decimal (coluna
            # Numeric) com float (quantidade) — TypeError. O db.session.refresh()
            # logo abaixo já cuida de sincronizar o objeto a partir do banco.
            .execution_options(synchronize_session=False)
        )
        if resultado.rowcount == 0:
            raise EstoqueInsuficienteError(f"estoque insuficiente para {produto.nome}")
        db.session.refresh(produto)
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
