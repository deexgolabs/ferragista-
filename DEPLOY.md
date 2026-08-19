# Guia de deploy — Ferragista+ no PythonAnywhere

Este guia assume uma conta PythonAnywhere (o plano gratuito "Beginner" já
funciona para validar o produto — só depois migre para um plano pago se
precisar de mais CPU/tráfego ou domínio próprio).

## Visão geral

No PythonAnywhere você não sobe um container: envia os arquivos do projeto
(via `git clone` ou upload), cria um virtualenv e configura **um único Web
App** que serve tanto o backend (Flask, via WSGI) quanto o frontend
(arquivos estáticos), no mesmo domínio `seu-usuario.pythonanywhere.com` —
isso evita problemas de CORS entre frontend e API.

- **Backend**: Flask rodando via WSGI (o próprio servidor do PythonAnywhere,
  não precisa de gunicorn — mas ele já está no `requirements.txt` para quem
  quiser rodar em outro provedor no futuro).
- **Banco de dados**: SQLite em `backend/instance/ferragista.db` funciona
  bem para começar (o Web App do PythonAnywhere roda em um único processo).
  Se crescer, o PythonAnywhere oferece um banco **MySQL** gerenciado por
  conta gratuita — instruções na seção 6.
- **Frontend**: servido como **arquivos estáticos** apontando direto para a
  pasta `frontend/`, sem build step.

## 1. Subir o código

No Bash console do PythonAnywhere:

```bash
cd ~
git clone <url-do-seu-repositorio> ferragista
# ou: suba os arquivos pela aba Files se não usar git
```

Se ainda não tiver um repositório Git, pode usar a aba **Files** do
PythonAnywhere para fazer upload do `.zip` do projeto e extrair com
`unzip ferragista.zip`.

## 2. Criar o virtualenv e instalar dependências

```bash
cd ~/ferragista/backend
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

(Use a versão de Python disponível na sua conta — confira em **Web → Python
version**; a mesma versão deve ser escolhida no passo 4.)

## 3. Configurar variáveis de ambiente

Copie e edite o `.env`:

```bash
cp .env.example .env
nano .env
```

No mínimo, gere valores novos para `SECRET_KEY` e `JWT_SECRET_KEY` (nunca
reuse os valores de exemplo) e ajuste `FRONTEND_URL` para
`https://seu-usuario.pythonanywhere.com`.

## 4. Criar o Web App

Na aba **Web** do painel do PythonAnywhere:

1. **Add a new web app** → escolha **Manual configuration** (não use os
   templates prontos de Flask, pois eles não fazem `load_dotenv` nem
   configuram a `app.config` do jeito que este projeto espera) → selecione
   a mesma versão de Python do passo 2.
2. Em **Code**:
   - **Source code**: `/home/seu-usuario/ferragista/backend`
   - **Working directory**: `/home/seu-usuario/ferragista/backend`
3. Em **Virtualenv**, informe: `/home/seu-usuario/ferragista/backend/venv`
4. Edite o **WSGI configuration file** (link na mesma página) e substitua o
   conteúdo por:

   ```python
   import sys
   import os

   project_home = '/home/seu-usuario/ferragista/backend'
   if project_home not in sys.path:
       sys.path.insert(0, project_home)

   os.chdir(project_home)

   from dotenv import load_dotenv
   load_dotenv(os.path.join(project_home, '.env'))

   from app import create_app
   application = create_app()
   ```

## 5. Mapear as pastas estáticas do frontend

Ainda na aba **Web**, em **Static files**, adicione uma entrada para cada
subpasta do frontend (isso faz o PythonAnywhere servir esses arquivos
diretamente, sem passar pelo Flask, e mantém `/api/...` livre para o WSGI):

| URL | Directory |
|---|---|
| `/pages/` | `/home/seu-usuario/ferragista/frontend/pages/` |
| `/css/` | `/home/seu-usuario/ferragista/frontend/css/` |
| `/js/` | `/home/seu-usuario/ferragista/frontend/js/` |
| `/assets/` | `/home/seu-usuario/ferragista/frontend/assets/` |

O app é um **PWA instalável** (celular e desktop) — isso exige mais duas
entradas apontando direto pros arquivos (não pastas), porque o
`manifest.json` e o `sw.js` (service worker) precisam ser servidos na
**raiz** do domínio, não dentro de `/pages` ou `/js`:

| URL | Directory |
|---|---|
| `/manifest.json` | `/home/seu-usuario/ferragista/frontend/manifest.json` |
| `/sw.js` | `/home/seu-usuario/ferragista/frontend/sw.js` |

Antes de sair, ajuste `API_BASE_URL` em `frontend/js/api.js` para
`https://seu-usuario.pythonanywhere.com/api` (mesmo domínio, então também dá
pra deixar como caminho relativo `/api` se preferir).

**Sobre HTTPS**: um service worker só funciona em contexto seguro —
`https://` ou `localhost`. O domínio `*.pythonanywhere.com` já vem com
HTTPS por padrão, então isso funciona sem configuração extra; só preste
atenção se um dia migrar para domínio próprio, que precisa de certificado.

Depois de configurar tudo, clique em **Reload** no topo da aba Web.

Acesse `https://seu-usuario.pythonanywhere.com/pages/login.html`.

## 6. Criar as tabelas do banco

No Bash console (com o virtualenv ativado, passo 2):

```bash
cd ~/ferragista/backend
source venv/bin/activate
python -c "from app import create_app; from app.extensions import db; app = create_app(); app.app_context().push(); db.create_all()"
flask --app run.py seed
```

Isso cria o super_admin `dono@ferragista.com` / `trocarSenha123` — troque a
senha no primeiro login em **Meu perfil**.

### Opcional: migrar para MySQL

O plano gratuito do PythonAnywhere já inclui um banco MySQL (aba
**Databases**). Se preferir usar em vez de SQLite:

```bash
pip install PyMySQL
```

E no `.env`:

```
DATABASE_URL=mysql+pymysql://seu-usuario:senha@seu-usuario.mysql.pythonanywhere-services.com/seu-usuario$ferragista
```

Rode novamente o `db.create_all()` (ou as migrações, se já tiver
versionado) apontando para o novo banco.

## 7. Tarefas agendadas (lembretes por e-mail)

Na aba **Tasks** do PythonAnywhere (disponível mesmo no plano gratuito —
mas com limite de 1 tarefa diária nesse plano; para rodar as três, um plano
pago é necessário), agende os comandos abaixo, 1x por dia cada:

```bash
cd /home/seu-usuario/ferragista/backend && venv/bin/python -m flask --app run.py avisar-trials
cd /home/seu-usuario/ferragista/backend && venv/bin/python -m flask --app run.py avisar-estoque-baixo
cd /home/seu-usuario/ferragista/backend && venv/bin/python -m flask --app run.py avisar-contas-vencendo
```

- `avisar-trials` — lembra lojas com trial expirando em 3 ou 1 dia
- `avisar-estoque-baixo` — lista para admin/gerente os produtos no ou abaixo do estoque mínimo
- `avisar-contas-vencendo` — lista contas a pagar/receber vencidas ou vencendo em até 3 dias

No plano gratuito, priorize `avisar-trials` (crítico para o negócio da
plataforma) ou combine as verificações num único script/cron externo que
chame os três comandos em sequência, se preferir não depender do agendador
interno do PythonAnywhere.

## 8. Checklist antes de ativar clientes reais

- [ ] `SECRET_KEY` e `JWT_SECRET_KEY` trocados no `.env` (nunca os valores de dev)
- [ ] Senha do super_admin trocada após o primeiro login
- [ ] `FRONTEND_URL` e `API_BASE_URL` apontando para o domínio real do PythonAnywhere (ou domínio customizado, se tiver um plano pago)
- [ ] Mapeamentos de **Static files** configurados e testados (`/pages`, `/css`, `/js`, `/assets`, `/manifest.json`, `/sw.js`)
- [ ] PWA instala de verdade: abra `https://seu-usuario.pythonanywhere.com/pages/login.html` no Chrome e confirme que aparece a opção de instalar (ícone na barra de endereço no desktop, ou o botão flutuante "Instalar app")
- [ ] E-mail configurado no `.env` (senão recuperação de senha só imprime no console de erros do Web App)
- [ ] HTTPS habilitado — já vem por padrão no domínio `*.pythonanywhere.com`
- [ ] Tarefa diária de `avisar-trials` agendada
- [ ] Backup periódico do arquivo `backend/instance/ferragista.db` (ou do banco MySQL, se migrar) — o PythonAnywhere não faz isso automaticamente

## Solução de problemas

- **Erro 502/500 ao acessar o site**: veja o **Error log** na aba Web —
  geralmente é caminho errado no WSGI file ou dependência faltando no
  virtualenv.
- **Frontend carrega mas não faz login**: confira se `API_BASE_URL` em
  `frontend/js/api.js` aponta para o domínio certo e se o mapeamento de
  `/pages`, `/css`, `/js` está correto (um `console.error` de rede na aba do
  navegador confirma isso rapidamente).
- **Alterações no código não aparecem**: depois de um `git pull` ou upload
  novo, sempre clique em **Reload** na aba Web — o WSGI não recarrega
  sozinho.
- **Opção de instalar o app não aparece**: confira se `/manifest.json` e
  `/sw.js` abrem direto no navegador (sem erro 404) e se o console não
  mostra erro ao registrar o service worker. Depois de qualquer alteração no
  `sw.js`, troque o valor de `CACHE_NAME` no arquivo — sem isso, quem já
  instalou o app continua servindo os arquivos antigos do cache.
