# Ferragista+ — Sistema de Gestão para Ferragistas

Backend em Python (Flask + SQLAlchemy + SQLite) e frontend em HTML, CSS e JS
puro, consumindo a API via `fetch`. Mesma arquitetura do IgrejaGo, adaptada
para o dia a dia de uma loja de ferragens/materiais de construção: estoque,
PDV, fornecedores/compras e financeiro.

## Estrutura de pastas

```
Ferragista/
├── backend/
│   ├── app/
│   │   ├── __init__.py        # application factory
│   │   ├── config.py
│   │   ├── extensions.py      # db, migrate, jwt, cors, mail, limiter
│   │   ├── models/             # Loja, Usuario, Produto, Categoria, MovimentacaoEstoque,
│   │   │                       #   Fornecedor, Cliente, Compra/CompraItem, Venda/VendaItem, Lancamento
│   │   ├── routes/             # blueprints (auth, publico, central, produtos, estoque,
│   │   │                       #   fornecedores, compras, clientes, vendas, financeiro, relatorios)
│   │   ├── services/           # regras de negócio compartilhadas (estoque_service)
│   │   └── utils/               # rbac, tenant, email
│   ├── instance/                # banco SQLite local (gitignored)
│   ├── migrations/              # migrações Alembic (Flask-Migrate)
│   ├── requirements.txt
│   ├── run.py
│   └── .env.example
├── frontend/
│   ├── css/style.css
│   ├── js/                      # api.js, auth.js, layout.js + um arquivo por módulo
│   ├── pages/                   # uma página HTML por módulo
│   └── assets/img/
└── docs/
```

## Como rodar o backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows (use `source venv/bin/activate` no Linux/Mac)
pip install -r requirements.txt
copy .env.example .env         # ajuste as chaves secretas (opcional em dev)
```

Como ainda não há migrações versionadas, crie as tabelas com:

```bash
python -c "from app import create_app; from app.extensions import db; app = create_app(); app.app_context().push(); db.create_all()"
```

(A partir da primeira alteração de modelo, use `flask --app run.py db init/migrate/upgrade` normalmente.)

```bash
flask --app run.py seed        # cria o super_admin: dono@ferragista.com / trocarSenha123
python run.py                  # roda em http://localhost:5000
```

**Troque a senha do super_admin no primeiro login.** Lojas clientes se
cadastram sozinhas em `/pages/cadastro-loja.html` — não crie lojas
manualmente no banco.

## Como rodar os testes

```bash
cd backend
pip install -r requirements-dev.txt   # instala pytest além das dependências normais
python -m pytest -v
```

A suíte (`backend/tests/`) cobre os fluxos que mexem em dinheiro e estoque —
os de maior risco num bug silencioso: isolamento multi-tenant (uma loja
nunca acessa dados de outra), baixa/entrada de estoque, venda à vista e
fiado (com saldo devedor do cliente), cancelamento com estorno, caixa
(abertura/fechamento, sangria/suprimento, valor esperado em dinheiro),
recebimento de compra gerando conta a pagar, e os relatórios (curva ABC,
margem, comissão). Cada teste roda contra um SQLite temporário isolado,
criado e descartado automaticamente — não toca no banco de desenvolvimento.

## Como rodar o frontend

O frontend é estático. Sirva com qualquer servidor HTTP simples:

```bash
cd frontend
python -m http.server 5500
```

Acesse `http://localhost:5500/pages/login.html`. Se o backend rodar em outra
porta/host, ajuste `API_BASE_URL` em `frontend/js/api.js`.

## Multi-tenant: uma instalação, várias lojas

O sistema é **SaaS multi-tenant** — uma única instalação atende várias
ferragistas clientes, cada uma com seus dados completamente isolados por
`loja_id`.

- **Loja (cliente)** se cadastra sozinha em `/pages/cadastro-loja.html`,
  começa em modo **trial** (14 dias) e ganha um usuário `admin` próprio.
- **`super_admin`** (você, dono do produto) não pertence a nenhuma loja —
  faz login normalmente e cai no **painel central**
  (`/pages/central-dashboard.html` e `/pages/central-lojas.html`), onde vê
  todas as lojas cadastradas e pode ativar, suspender ou trocar o plano de
  cada uma manualmente (sem gateway de pagamento integrado ainda).
- Toda rota de dados da loja (`/api/produtos`, `/api/vendas`, etc.) é
  automaticamente filtrada pelo `loja_id` do token JWT — uma loja nunca
  acessa dados de outra (`app/utils/tenant.py`).
- Se a loja for suspensa/expirar o trial, o login dos usuários dela é
  bloqueado com uma mensagem clara, até o `super_admin` reativar.

## Perfis de usuário e controle de acesso

| Perfil | Acesso |
|---|---|
| `super_admin` | Dono da plataforma — painel central, gestão de todas as lojas. Não vê dados internos de nenhuma loja. |
| `admin` | Acesso total **dentro da própria loja**, incluindo gestão de usuários |
| `gerente` | Acesso total à loja, exceto gestão de usuários |
| `estoquista` | Produtos, estoque, fornecedores e compras |
| `vendedor` | PDV/vendas e clientes |

O `super_admin` é criado pelo comando `seed`. Dentro de cada loja, novos
usuários só podem ser cadastrados por um `admin` daquela loja, na página
**Usuários**.

## Módulos implementados

- **Autenticação** — login com JWT, perfis de usuário, recuperação de senha por e-mail, troca de senha e edição dos próprios dados em **Meu perfil**, rate limiting no login
- **Produtos** — cadastro com código/SKU, categoria, unidade de medida, preço de custo/venda, estoque mínimo com alerta de estoque baixo
- **Importação de produtos via CSV** — cadastro em lote (`nome,codigo,categoria,unidade,preco_custo,preco_venda,quantidade_estoque,estoque_minimo`), cria categorias novas automaticamente e reporta erros linha a linha sem interromper a importação
- **Estoque** — movimentações manuais (entrada/saída/ajuste) com histórico e motivo; baixa automática nas vendas e entrada automática no recebimento de compras
- **PDV / Vendas** — leitor de código de barras dedicado (campo com autofoco, adiciona ao carrinho ao pressionar Enter — funciona com scanner USB "tipo teclado"), busca por nome/código, carrinho, desconto, formas de pagamento (dinheiro, PIX, cartão débito/crédito, fiado), baixa de estoque e lançamento financeiro automáticos, cancelamento com estorno, cupom/recibo imprimível (`recibo-venda.html`, via impressão do navegador)
- **Caixa** — abertura/fechamento de sessão com valor inicial, sangria e suprimento, resumo de vendas por forma de pagamento e cálculo do valor esperado em dinheiro na gaveta; vendas se vinculam automaticamente à sessão aberta
- **Etiquetas com código de barras** — geração server-side (CODE128) por produto, seleção em lote com quantidade de cópias e impressão em grade (`etiquetas.html`)
- **Clientes** — cadastro com limite de fiado e saldo devedor atualizado automaticamente pelas vendas fiado
- **Fornecedores** — cadastro completo (CNPJ, contato, endereço)
- **Compras** — pedido de compra com múltiplos itens; ao receber, dá entrada no estoque e gera conta a pagar automaticamente
- **Financeiro** — lançamentos manuais de entrada/saída, contas a pagar/receber (quitação), resumo (entradas, saídas, saldo, a receber/a pagar)
- **Relatórios** — painel geral, produtos mais vendidos, vendas por período, estoque baixo, curva ABC de produtos, margem de lucro (total e por produto), comissão de vendedores por percentual configurável por usuário
- **Notificações in-app** — sininho no menu lateral com estoque baixo e contas a pagar/receber vencidas ou vencendo em até 3 dias
- **Notificações proativas por e-mail** — comandos CLI diários (`avisar-trials`, `avisar-estoque-baixo`, `avisar-contas-vencendo`) para agendar via tarefa agendada do servidor
- **Nota fiscal (estrutura, não emite de verdade)** — tela para guardar configuração de um provedor terceiro (Focus NFe/PlugNotas/eNotas) para quando a emissão fiscal for implementada; **não há integração real com a SEFAZ** — isso exige certificado digital e é um desenvolvimento futuro
- **Multi-tenant SaaS** — cadastro self-service com trial, painel central do dono da plataforma
- **Modo escuro** — alternância persistida por usuário
- **PWA instalável** — manifest.json + service worker, instala no celular (Android/iOS) e no desktop (Chrome/Edge) com botão flutuante de instalação; app shell (CSS/JS) funciona offline em telas já visitadas, chamadas de API nunca são cacheadas
- **Responsivo** — menu lateral vira gaveta (hambúrguer) abaixo de 860px, formulários/tabelas se adaptam a telas pequenas, sem zoom indesejado em inputs no iOS

## Integrações opcionais (e-mail)

E-mail (recuperação de senha, boas-vindas) já está implementado, mas exige
credenciais próprias no `.env` do backend para funcionar de verdade. **Sem
configurar nada, o sistema funciona normalmente** — e-mails são apenas
impressos no console do servidor (modo desenvolvimento).

Configure `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`,
`MAIL_DEFAULT_SENDER` no `.env` para envio real. Veja `backend/.env.example`.

## Comandos agendados (CLI)

```bash
flask --app run.py avisar-trials             # lembretes de trial expirando (1x/dia)
flask --app run.py avisar-estoque-baixo      # e-mail de produtos com estoque baixo (1x/dia)
flask --app run.py avisar-contas-vencendo    # e-mail de contas a pagar/receber vencendo (1x/dia)
```

## Planos e limites

Cada loja tem um plano (`gratuito`, `basico`, `premium`) com limite de
produtos cadastrados (`app/models/loja.py`, `LIMITES_PLANO`). Cadastrar um
produto acima do limite retorna erro 402. A troca de plano é sempre manual
pelo `super_admin` no painel central — não há gateway de pagamento
integrado ainda.

## Deploy

Veja [`DEPLOY.md`](DEPLOY.md) — guia específico para publicar no
PythonAnywhere.

## Ideias de próximos passos

- Emissão de nota fiscal eletrônica de verdade (NF-e/NFC-e) — a tela de configuração já existe (`/pages/nota-fiscal.html`), falta implementar a chamada real a um provedor (Focus NFe/PlugNotas/eNotas) usando a chave de API salva
- Gateway de pagamento (Stripe/Mercado Pago) integrado ao painel central, para automatizar a ativação hoje feita manualmente pelo `super_admin`
- Impressão de cupom/etiqueta em impressora térmica dedicada (hoje a impressão é via diálogo de impressão do navegador)
- Migrações Alembic versionadas — hoje o banco é criado via `db.create_all()`, sem histórico de schema (testes automatizados já existem, veja "Como rodar os testes")
