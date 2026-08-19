import os
from datetime import date, timedelta

from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.extensions import db
from app.models import Usuario, Loja, Produto, Lancamento, Categoria, Cliente, Fornecedor
from app.utils.email import enviar_email

app = create_app()


@app.cli.command("seed")
def seed():
    """Cria o super_admin (dono da plataforma) — flask --app run.py seed.

    O super_admin não pertence a nenhuma loja (loja_id=None); ele enxerga e
    administra todas as lojas pelo painel central. Lojas clientes se
    cadastram sozinhas em /pages/cadastro-loja.html."""
    if Usuario.query.filter_by(email="dono@ferragista.com").first():
        print("Usuário super_admin já existe.")
        return

    dono = Usuario(nome="Dono do Ferragista+", email="dono@ferragista.com", perfil="super_admin", loja_id=None)
    dono.set_senha("trocarSenha123")
    db.session.add(dono)
    db.session.commit()
    print("Super admin criado: dono@ferragista.com / trocarSenha123 — troque a senha após o primeiro login.")


@app.cli.command("seed-demo")
def seed_demo():
    """Cria uma loja de demonstração já com produtos/cliente/fornecedor de
    exemplo — flask --app run.py seed-demo. Útil pra mostrar o sistema sem
    precisar passar pelo cadastro público antes."""
    email = "demo@ferragista.com"
    if Usuario.query.filter_by(email=email).first():
        print("Loja demo já existe. Login: demo@ferragista.com / demo1234")
        return

    loja = Loja(
        nome="Ferragem Demo",
        email_contato=email,
        plano="premium",
        status="ativa",
    )
    db.session.add(loja)
    db.session.flush()

    admin = Usuario(nome="Admin Demo", email=email, perfil="admin", loja_id=loja.id)
    admin.set_senha("demo1234")
    db.session.add(admin)

    categoria = Categoria(loja_id=loja.id, nome="Ferramentas")
    db.session.add(categoria)
    db.session.flush()

    produtos = [
        Produto(loja_id=loja.id, categoria_id=categoria.id, nome="Parafuso 3/4", codigo="P001",
                unidade="un", preco_custo=0.10, preco_venda=0.25, quantidade_estoque=500, estoque_minimo=50),
        Produto(loja_id=loja.id, categoria_id=categoria.id, nome="Martelo", codigo="M001",
                unidade="un", preco_custo=10.00, preco_venda=25.90, quantidade_estoque=15, estoque_minimo=20),
        Produto(loja_id=loja.id, categoria_id=categoria.id, nome="Prego 18x27", codigo="PR18",
                unidade="kg", preco_custo=4.50, preco_venda=8.90, quantidade_estoque=50, estoque_minimo=5),
        Produto(loja_id=loja.id, categoria_id=categoria.id, nome="Trena 5m", codigo="T005",
                unidade="un", preco_custo=8.00, preco_venda=19.90, quantidade_estoque=2, estoque_minimo=3),
    ]
    db.session.add_all(produtos)

    cliente = Cliente(loja_id=loja.id, nome="Cliente Exemplo", telefone="(11) 99999-0000", limite_fiado=500)
    db.session.add(cliente)

    fornecedor = Fornecedor(loja_id=loja.id, nome="Distribuidora Exemplo Ltda", telefone="(11) 3333-0000")
    db.session.add(fornecedor)

    db.session.commit()
    print("Loja demo criada — login: demo@ferragista.com / demo1234")
    print("(Trena 5m e Martelo já estão com estoque baixo de propósito, pra mostrar os alertas.)")


@app.cli.command("avisar-trials")
def avisar_trials():
    """Envia e-mail para lojas com trial expirando em 3 ou 1 dia.

    Rode uma vez por dia via tarefa agendada:
      flask --app run.py avisar-trials
    """
    hoje = date.today()
    alvos = [hoje + timedelta(days=3), hoje + timedelta(days=1)]

    lojas = Loja.query.filter(
        Loja.status == "trial",
        Loja.trial_expira_em.in_(alvos),
    ).all()

    enviados = 0
    for loja in lojas:
        if loja.lembrete_enviado_em == hoje:
            continue

        dias_restantes = (loja.trial_expira_em - hoje).days
        admin = Usuario.query.filter_by(loja_id=loja.id, perfil="admin").first()
        if not admin:
            continue

        enviar_email(
            admin.email,
            f"Seu teste grátis do Ferragista+ termina em {dias_restantes} dia(s)",
            f"Olá, {admin.nome}!\n\nO período de teste da {loja.nome} termina em "
            f"{dias_restantes} dia(s) ({loja.trial_expira_em.strftime('%d/%m/%Y')}). "
            f"Para continuar usando sem interrupção, entre em contato para ativar um plano pago.",
        )
        loja.lembrete_enviado_em = hoje
        enviados += 1

    db.session.commit()
    print(f"{enviados} lembrete(s) de trial enviado(s).")


@app.cli.command("avisar-estoque-baixo")
def avisar_estoque_baixo():
    """Envia e-mail para admin/gerente de cada loja com produtos abaixo do
    estoque mínimo. Rode uma vez por dia via tarefa agendada:
      flask --app run.py avisar-estoque-baixo
    """
    lojas = Loja.query.filter(Loja.status.in_(["trial", "ativa"])).all()
    enviados = 0

    for loja in lojas:
        produtos = Produto.query.filter(
            Produto.loja_id == loja.id, Produto.ativo == True, Produto.quantidade_estoque <= Produto.estoque_minimo
        ).order_by(Produto.nome).all()
        if not produtos:
            continue

        linhas = "\n".join(f"  - {p.nome}: {p.quantidade_estoque} {p.unidade} (mínimo: {p.estoque_minimo} {p.unidade})" for p in produtos)
        corpo = f"Os seguintes produtos estão com estoque igual ou abaixo do mínimo:\n\n{linhas}"

        destinatarios = Usuario.query.filter(Usuario.loja_id == loja.id, Usuario.perfil.in_(["admin", "gerente"])).all()
        for destinatario in destinatarios:
            enviar_email(destinatario.email, f"Estoque baixo — {loja.nome}", f"Olá, {destinatario.nome}!\n\n{corpo}")
            enviados += 1

    print(f"{enviados} e-mail(s) de estoque baixo enviado(s).")


@app.cli.command("avisar-contas-vencendo")
def avisar_contas_vencendo():
    """Envia e-mail para admin/gerente de cada loja com contas a pagar/receber
    vencidas ou vencendo nos próximos 3 dias. Rode uma vez por dia:
      flask --app run.py avisar-contas-vencendo
    """
    hoje = date.today()
    limite = hoje + timedelta(days=3)
    lojas = Loja.query.filter(Loja.status.in_(["trial", "ativa"])).all()
    enviados = 0

    for loja in lojas:
        contas = Lancamento.query.filter(
            Lancamento.loja_id == loja.id,
            Lancamento.status == "pendente",
            Lancamento.vencimento.isnot(None),
            Lancamento.vencimento <= limite,
        ).order_by(Lancamento.vencimento).all()
        if not contas:
            continue

        linhas = []
        for conta in contas:
            tipo_texto = "a receber" if conta.tipo == "entrada" else "a pagar"
            prazo = "vencida" if conta.vencimento < hoje else f"vence em {(conta.vencimento - hoje).days} dia(s)"
            linhas.append(f"  - {conta.descricao or conta.categoria} ({tipo_texto}, {prazo}): R$ {float(conta.valor):.2f}")
        corpo = "As seguintes contas precisam de atenção:\n\n" + "\n".join(linhas)

        destinatarios = Usuario.query.filter(Usuario.loja_id == loja.id, Usuario.perfil.in_(["admin", "gerente"])).all()
        for destinatario in destinatarios:
            enviar_email(destinatario.email, f"Contas a vencer — {loja.nome}", f"Olá, {destinatario.nome}!\n\n{corpo}")
            enviados += 1

    print(f"{enviados} e-mail(s) de contas a vencer enviado(s).")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=port)
