from datetime import date, datetime, timedelta

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy import func

from app.extensions import db
from app.models.venda import Venda, VendaItem
from app.models.produto import Produto
from app.models.financeiro import Lancamento
from app.models.usuario import Usuario
from app.utils.rbac import perfis_permitidos
from app.utils.tenant import loja_atual_id

relatorios_bp = Blueprint("relatorios", __name__)


@relatorios_bp.get("/notificacoes")
@jwt_required()
def notificacoes():
    """Alertas para o sininho do menu: produtos com estoque baixo e contas
    a pagar/receber vencidas ou vencendo nos próximos 3 dias. Limitado a
    um total razoável de itens para não virar uma lista infinita."""
    loja_id = loja_atual_id()
    hoje = date.today()
    limite_vencimento = hoje + timedelta(days=3)

    itens = []

    produtos_baixo = (
        Produto.query.filter(
            Produto.loja_id == loja_id, Produto.ativo == True, Produto.quantidade_estoque <= Produto.estoque_minimo
        )
        .order_by(Produto.nome)
        .limit(10)
        .all()
    )
    for produto in produtos_baixo:
        itens.append(
            {
                "tipo": "estoque_baixo",
                "mensagem": f"Estoque baixo: {produto.nome} ({produto.quantidade_estoque} {produto.unidade})",
                "url": "produtos.html",
            }
        )

    if get_jwt().get("perfil") in ("admin", "gerente"):
        contas = (
            Lancamento.query.filter(
                Lancamento.loja_id == loja_id,
                Lancamento.status == "pendente",
                Lancamento.vencimento.isnot(None),
                Lancamento.vencimento <= limite_vencimento,
            )
            .order_by(Lancamento.vencimento)
            .limit(10)
            .all()
        )
        for conta in contas:
            atrasada = conta.vencimento < hoje
            tipo_texto = "receber" if conta.tipo == "entrada" else "pagar"
            prazo = "vencida" if atrasada else f"vence em {(conta.vencimento - hoje).days} dia(s)"
            itens.append(
                {
                    "tipo": "conta_vencendo",
                    "mensagem": f"Conta a {tipo_texto} {prazo}: {conta.descricao or conta.categoria} — R$ {float(conta.valor):.2f}",
                    "url": "financeiro.html",
                }
            )

    return jsonify(itens[:20])


@relatorios_bp.get("/dashboard")
@jwt_required()
def dashboard():
    loja_id = loja_atual_id()
    hoje = date.today()
    inicio_hoje = datetime.combine(hoje, datetime.min.time())
    inicio_mes = datetime.combine(hoje.replace(day=1), datetime.min.time())

    vendas_hoje = Venda.query.filter(
        Venda.loja_id == loja_id, Venda.status == "concluida", Venda.criado_em >= inicio_hoje
    ).all()
    vendas_mes = Venda.query.filter(
        Venda.loja_id == loja_id, Venda.status == "concluida", Venda.criado_em >= inicio_mes
    ).all()

    total_produtos = Produto.query.filter_by(loja_id=loja_id, ativo=True).count()
    produtos_estoque_baixo = Produto.query.filter(
        Produto.loja_id == loja_id, Produto.ativo == True, Produto.quantidade_estoque <= Produto.estoque_minimo
    ).count()

    lancamentos_pagos = Lancamento.query.filter_by(loja_id=loja_id, status="pago").all()
    saldo = sum(float(l.valor) if l.tipo == "entrada" else -float(l.valor) for l in lancamentos_pagos)

    a_receber = sum(
        float(l.valor)
        for l in Lancamento.query.filter_by(loja_id=loja_id, status="pendente", tipo="entrada").all()
    )
    a_pagar = sum(
        float(l.valor)
        for l in Lancamento.query.filter_by(loja_id=loja_id, status="pendente", tipo="saida").all()
    )

    return jsonify(
        {
            "vendas_hoje_total": round(sum(v.total() for v in vendas_hoje), 2),
            "vendas_hoje_quantidade": len(vendas_hoje),
            "vendas_mes_total": round(sum(v.total() for v in vendas_mes), 2),
            "vendas_mes_quantidade": len(vendas_mes),
            "total_produtos_ativos": total_produtos,
            "produtos_estoque_baixo": produtos_estoque_baixo,
            "saldo_financeiro": round(saldo, 2),
            "a_receber": round(a_receber, 2),
            "a_pagar": round(a_pagar, 2),
        }
    )


@relatorios_bp.get("/produtos-mais-vendidos")
@jwt_required()
def produtos_mais_vendidos():
    loja_id = loja_atual_id()
    dias = request.args.get("dias", 30, type=int)
    desde = datetime.now() - timedelta(days=dias)

    resultado = (
        db.session.query(
            VendaItem.produto_id,
            func.sum(VendaItem.quantidade).label("quantidade_total"),
            func.sum(VendaItem.quantidade * VendaItem.preco_unitario).label("valor_total"),
        )
        .join(Venda, Venda.id == VendaItem.venda_id)
        .filter(Venda.loja_id == loja_id, Venda.status == "concluida", Venda.criado_em >= desde)
        .group_by(VendaItem.produto_id)
        .order_by(func.sum(VendaItem.quantidade).desc())
        .limit(10)
        .all()
    )

    nomes = {p.id: p.nome for p in Produto.query.filter_by(loja_id=loja_id).all()}
    return jsonify(
        [
            {
                "produto_id": produto_id,
                "produto_nome": nomes.get(produto_id, "?"),
                "quantidade_total": float(quantidade_total),
                "valor_total": round(float(valor_total), 2),
            }
            for produto_id, quantidade_total, valor_total in resultado
        ]
    )


@relatorios_bp.get("/vendas-por-periodo")
@perfis_permitidos("admin", "gerente")
def vendas_por_periodo():
    loja_id = loja_atual_id()
    dias = request.args.get("dias", 30, type=int)
    desde = datetime.now() - timedelta(days=dias)

    vendas = Venda.query.filter(
        Venda.loja_id == loja_id, Venda.status == "concluida", Venda.criado_em >= desde
    ).all()

    por_dia: dict[str, float] = {}
    for venda in vendas:
        chave = venda.criado_em.strftime("%Y-%m-%d")
        por_dia[chave] = por_dia.get(chave, 0.0) + venda.total()

    return jsonify(dict(sorted(por_dia.items())))


@relatorios_bp.get("/estoque-baixo")
@jwt_required()
def estoque_baixo():
    loja_id = loja_atual_id()
    produtos = Produto.query.filter(
        Produto.loja_id == loja_id, Produto.ativo == True, Produto.quantidade_estoque <= Produto.estoque_minimo
    ).order_by(Produto.nome).all()
    return jsonify([p.to_dict() for p in produtos])


@relatorios_bp.get("/curva-abc")
@perfis_permitidos("admin", "gerente")
def curva_abc():
    """Classifica os produtos vendidos no período pela contribuição
    acumulada de faturamento: A = até 80% do total, B = até 95%, C = resto —
    a régua clássica de curva ABC de estoque."""
    loja_id = loja_atual_id()
    dias = request.args.get("dias", 30, type=int)
    desde = datetime.now() - timedelta(days=dias)

    resultado = (
        db.session.query(
            VendaItem.produto_id,
            func.sum(VendaItem.quantidade * VendaItem.preco_unitario).label("valor_total"),
        )
        .join(Venda, Venda.id == VendaItem.venda_id)
        .filter(Venda.loja_id == loja_id, Venda.status == "concluida", Venda.criado_em >= desde)
        .group_by(VendaItem.produto_id)
        .order_by(func.sum(VendaItem.quantidade * VendaItem.preco_unitario).desc())
        .all()
    )

    nomes = {p.id: p.nome for p in Produto.query.filter_by(loja_id=loja_id).all()}
    valor_total_geral = sum(float(valor) for _, valor in resultado) or 1.0

    itens = []
    acumulado = 0.0
    for produto_id, valor in resultado:
        valor = float(valor)
        # Classe decidida pelo acumulado ANTES de somar este item: assim, o
        # item que faz o acumulado cruzar de 79% para 100% (ex: único
        # produto vendido) continua na classe de quem "abriu" a faixa, em
        # vez de cair para C só por ter fechado a soma.
        percentual_acumulado_antes = acumulado / valor_total_geral * 100
        if percentual_acumulado_antes <= 80:
            classe = "A"
        elif percentual_acumulado_antes <= 95:
            classe = "B"
        else:
            classe = "C"

        acumulado += valor
        percentual_acumulado = acumulado / valor_total_geral * 100

        itens.append(
            {
                "produto_id": produto_id,
                "produto_nome": nomes.get(produto_id, "?"),
                "valor_total": round(valor, 2),
                "percentual_do_total": round(valor / valor_total_geral * 100, 2),
                "percentual_acumulado": round(percentual_acumulado, 2),
                "classe": classe,
            }
        )

    return jsonify(itens)


@relatorios_bp.get("/margem")
@perfis_permitidos("admin", "gerente")
def margem():
    """Margem de lucro (preço de venda − preço de custo) das vendas
    concluídas no período, no total e por produto."""
    loja_id = loja_atual_id()
    dias = request.args.get("dias", 30, type=int)
    desde = datetime.now() - timedelta(days=dias)

    itens = (
        db.session.query(VendaItem, Produto)
        .join(Venda, Venda.id == VendaItem.venda_id)
        .join(Produto, Produto.id == VendaItem.produto_id)
        .filter(Venda.loja_id == loja_id, Venda.status == "concluida", Venda.criado_em >= desde)
        .all()
    )

    receita_total = 0.0
    custo_total = 0.0
    por_produto: dict[int, dict] = {}

    for item, produto in itens:
        quantidade = float(item.quantidade)
        receita = quantidade * float(item.preco_unitario)
        custo = quantidade * float(produto.preco_custo or 0)
        receita_total += receita
        custo_total += custo

        acumulado = por_produto.setdefault(
            produto.id, {"produto_id": produto.id, "produto_nome": produto.nome, "receita": 0.0, "custo": 0.0}
        )
        acumulado["receita"] += receita
        acumulado["custo"] += custo

    por_produto_lista = []
    for dados in por_produto.values():
        margem_valor = dados["receita"] - dados["custo"]
        margem_percentual = (margem_valor / dados["receita"] * 100) if dados["receita"] else 0
        por_produto_lista.append(
            {
                "produto_id": dados["produto_id"],
                "produto_nome": dados["produto_nome"],
                "receita": round(dados["receita"], 2),
                "custo": round(dados["custo"], 2),
                "margem": round(margem_valor, 2),
                "margem_percentual": round(margem_percentual, 2),
            }
        )
    por_produto_lista.sort(key=lambda item: item["margem"], reverse=True)

    margem_total = receita_total - custo_total
    return jsonify(
        {
            "receita_total": round(receita_total, 2),
            "custo_total": round(custo_total, 2),
            "margem_total": round(margem_total, 2),
            "margem_percentual": round((margem_total / receita_total * 100) if receita_total else 0, 2),
            "por_produto": por_produto_lista,
        }
    )


@relatorios_bp.get("/comissoes")
@perfis_permitidos("admin", "gerente")
def comissoes():
    """Comissão devida a cada vendedor no período, com base no
    `percentual_comissao` cadastrado no usuário e no total vendido por ele."""
    loja_id = loja_atual_id()
    dias = request.args.get("dias", 30, type=int)
    desde = datetime.now() - timedelta(days=dias)

    vendas = Venda.query.filter(
        Venda.loja_id == loja_id, Venda.status == "concluida", Venda.criado_em >= desde
    ).all()

    totais_por_usuario: dict[int, float] = {}
    for venda in vendas:
        if not venda.usuario_id:
            continue
        totais_por_usuario[venda.usuario_id] = totais_por_usuario.get(venda.usuario_id, 0.0) + venda.total()

    usuarios = {u.id: u for u in Usuario.query.filter_by(loja_id=loja_id).all()}

    resultado = []
    for usuario_id, total_vendido in totais_por_usuario.items():
        usuario = usuarios.get(usuario_id)
        if not usuario:
            continue
        percentual = float(usuario.percentual_comissao)
        resultado.append(
            {
                "usuario_id": usuario_id,
                "usuario_nome": usuario.nome,
                "total_vendido": round(total_vendido, 2),
                "percentual_comissao": percentual,
                "comissao_devida": round(total_vendido * percentual / 100, 2),
            }
        )
    resultado.sort(key=lambda item: item["total_vendido"], reverse=True)
    return jsonify(resultado)
