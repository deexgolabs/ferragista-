function obterUsuarioLogado() {
  try {
    return JSON.parse(localStorage.getItem("usuario")) || {};
  } catch {
    return {};
  }
}

function iniciaisUsuario(nome) {
  if (!nome) return "?";
  const partes = nome.trim().split(/\s+/);
  const iniciais = partes.length > 1 ? partes[0][0] + partes[partes.length - 1][0] : partes[0][0];
  return iniciais.toUpperCase();
}

function slugGrupo(titulo) {
  return titulo
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

function grupoAbertoSalvo() {
  try {
    return localStorage.getItem("menu_grupo_aberto") || null;
  } catch {
    return null;
  }
}

function alternarGrupoMenu(id) {
  const grupos = Array.from(document.querySelectorAll(".menu-grupo"));
  const elemento = grupos.find((el) => el.dataset.grupo === id);
  if (!elemento) return;
  const vaiAbrir = elemento.classList.contains("recolhido");

  grupos.forEach((el) => {
    const aberto = vaiAbrir && el.dataset.grupo === id;
    el.classList.toggle("recolhido", !aberto);
    const botao = el.querySelector(".menu-grupo-titulo");
    if (botao) botao.setAttribute("aria-expanded", String(aberto));
  });

  localStorage.setItem("menu_grupo_aberto", vaiAbrir ? id : "");
}

function montarBarraLateral(paginaAtiva) {
  const usuario = obterUsuarioLogado();
  const perfil = usuario.perfil;

  const grupos = [
    {
      titulo: "Início",
      links: [
        { href: "dashboard.html", texto: "Painel", chave: "dashboard", icone: "home" },
        { href: "relatorios.html", texto: "Relatórios", chave: "relatorios", icone: "barChart" },
      ],
    },
    {
      titulo: "Vendas",
      links: [
        { href: "vendas.html", texto: "PDV / Vendas", chave: "vendas", icone: "cart" },
        { href: "caixa.html", texto: "Caixa", chave: "caixa", icone: "dollar" },
        { href: "clientes.html", texto: "Clientes", chave: "clientes", icone: "users" },
      ],
    },
    {
      titulo: "Estoque",
      links: [
        { href: "produtos.html", texto: "Produtos", chave: "produtos", icone: "wrench" },
        { href: "estoque.html", texto: "Movimentações", chave: "estoque", icone: "box" },
        { href: "etiquetas.html", texto: "Etiquetas", chave: "etiquetas", icone: "tag", perfis: ["admin", "gerente", "estoquista"] },
        { href: "fornecedores.html", texto: "Fornecedores", chave: "fornecedores", icone: "truck", perfis: ["admin", "gerente", "estoquista"] },
        { href: "compras.html", texto: "Compras", chave: "compras", icone: "tag", perfis: ["admin", "gerente", "estoquista"] },
      ],
    },
    {
      titulo: "Financeiro",
      links: [
        { href: "financeiro.html", texto: "Financeiro", chave: "financeiro", icone: "dollar", perfis: ["admin", "gerente"] },
      ],
    },
    {
      titulo: "Administração",
      links: [
        { href: "usuarios.html", texto: "Usuários", chave: "usuarios", icone: "shield", perfis: ["admin"] },
        { href: "nota-fiscal.html", texto: "Nota fiscal", chave: "nota-fiscal", icone: "fileText", perfis: ["admin", "gerente"] },
      ],
    },
  ];

  const grupoComPaginaAtiva = grupos.find((grupo) => grupo.links.some((link) => link.chave === paginaAtiva));
  const idGrupoParaAbrir = grupoComPaginaAtiva ? slugGrupo(grupoComPaginaAtiva.titulo) : grupoAbertoSalvo();

  const gruposHtml = grupos
    .map((grupo) => {
      const links = grupo.links.filter((link) => !link.perfis || link.perfis.includes(perfil));
      if (links.length === 0) return "";

      const id = slugGrupo(grupo.titulo);
      const aberto = id === idGrupoParaAbrir;

      const itens = links
        .map(
          (link) => `
            <a href="${link.href}" class="item-menu ${link.chave === paginaAtiva ? "ativo" : ""}">
              <span class="item-menu-icone">${svgIcone(link.icone)}</span>${link.texto}
            </a>
          `
        )
        .join("");

      return `
        <div class="menu-grupo ${aberto ? "" : "recolhido"}" data-grupo="${id}">
          <button type="button" class="menu-grupo-titulo" onclick="alternarGrupoMenu('${id}')" aria-expanded="${aberto}">
            <span>${grupo.titulo}</span>
            <span class="menu-grupo-seta">${svgIcone("chevronDown")}</span>
          </button>
          <div class="menu-grupo-itens">${itens}</div>
        </div>
      `;
    })
    .join("");

  return `
    <aside class="barra-lateral" id="barra-lateral-menu">
      <div class="marca">
        <div class="marca-icone">${svgIcone("wrench")}</div>
        <div class="marca-texto">
          <strong>Ferragista+</strong>
          <span>Gestão para ferragistas</span>
        </div>
      </div>

      <nav class="menu-nav">${gruposHtml}</nav>

      <div class="rodape-menu">
        <div class="utilitarios-menu">
          <div class="notificacoes-wrapper">
            <button type="button" class="btn-icone" id="btn-notificacoes" aria-label="Notificações">
              ${svgIcone("bell")}<span class="contador-notificacoes oculto" id="contador-notificacoes"></span>
            </button>
            <div class="dropdown-notificacoes oculto" id="dropdown-notificacoes">
              <strong>Notificações</strong>
              <div id="lista-notificacoes"><p class="sem-notificacoes">Sem novidades por aqui.</p></div>
            </div>
          </div>
          <button type="button" class="btn-icone" id="btn-alternar-tema" aria-label="Alternar tema">${svgIcone("moon")}</button>
        </div>
        <div class="usuario-info">
          <div class="avatar">${iniciaisUsuario(usuario.nome)}</div>
          <div class="usuario-textos">
            <strong>${usuario.nome || "Usuário"}</strong>
            <span>${usuario.perfil || ""}</span>
          </div>
        </div>
        <a href="meu-perfil.html" class="item-menu ${paginaAtiva === "meu-perfil" ? "ativo" : ""}">
          <span class="item-menu-icone">${svgIcone("userCircle")}</span>Meu perfil
        </a>
        <a href="#" onclick="sair(); return false;" class="item-menu">
          <span class="item-menu-icone">${svgIcone("logOut")}</span>Sair
        </a>
      </div>
    </aside>
  `;
}

async function carregarNotificacoesMenu() {
  const botao = document.getElementById("btn-notificacoes");
  if (!botao) return;
  try {
    const itens = await Api.notificacoes();
    const contador = document.getElementById("contador-notificacoes");
    const lista = document.getElementById("lista-notificacoes");

    if (itens.length > 0) {
      contador.textContent = itens.length;
      contador.classList.remove("oculto");
      lista.innerHTML = itens.map((n) => `<a href="${n.url}" class="item-notificacao">${n.mensagem}</a>`).join("");
    } else {
      contador.classList.add("oculto");
      lista.innerHTML = '<p class="sem-notificacoes">Sem novidades por aqui.</p>';
    }
  } catch {
    // silencioso: notificações não são essenciais para o uso da página
  }
}

function iniciarUtilitariosMenu() {
  const botaoTema = document.getElementById("btn-alternar-tema");
  if (botaoTema) {
    botaoTema.innerHTML = svgIcone((document.documentElement.getAttribute("data-tema") || "claro") === "escuro" ? "sun" : "moon");
    botaoTema.addEventListener("click", alternarTema);
  }

  const botaoNotificacoes = document.getElementById("btn-notificacoes");
  const dropdown = document.getElementById("dropdown-notificacoes");
  if (botaoNotificacoes && dropdown) {
    botaoNotificacoes.addEventListener("click", (evento) => {
      evento.stopPropagation();
      dropdown.classList.toggle("oculto");
    });
    document.addEventListener("click", (evento) => {
      if (!dropdown.contains(evento.target) && evento.target !== botaoNotificacoes) {
        dropdown.classList.add("oculto");
      }
    });
    carregarNotificacoesMenu();
  }
}

function alternarMenuMobile(abrir) {
  const barra = document.getElementById("barra-lateral-menu");
  const fundo = document.getElementById("fundo-menu-mobile");
  if (!barra || !fundo) return;
  barra.classList.toggle("aberta", abrir);
  fundo.classList.toggle("aberto", abrir);
}

document.addEventListener("DOMContentLoaded", () => {
  exigirAutenticacao();
  const alvo = document.getElementById("barra-lateral");
  if (alvo) {
    window.__paginaAtiva = alvo.dataset.pagina;
    alvo.outerHTML = montarBarraLateral(alvo.dataset.pagina);

    const conteudoPrincipal = document.querySelector("main.conteudo");
    if (conteudoPrincipal) {
      conteudoPrincipal.id = conteudoPrincipal.id || "conteudo-principal";
      conteudoPrincipal.setAttribute("tabindex", "-1");
      const linkPular = document.createElement("a");
      linkPular.href = `#${conteudoPrincipal.id}`;
      linkPular.className = "link-pular-conteudo";
      linkPular.textContent = "Pular para o conteúdo";
      document.body.prepend(linkPular);
    }

    const botaoMenu = document.createElement("button");
    botaoMenu.className = "btn-menu-mobile";
    botaoMenu.setAttribute("aria-label", "Abrir menu");
    botaoMenu.innerHTML = svgIcone("menu");
    botaoMenu.addEventListener("click", () => alternarMenuMobile(true));
    document.body.prepend(botaoMenu);

    const fundo = document.createElement("div");
    fundo.id = "fundo-menu-mobile";
    fundo.className = "fundo-menu-mobile";
    fundo.addEventListener("click", () => alternarMenuMobile(false));
    document.body.prepend(fundo);

    document.getElementById("barra-lateral-menu").addEventListener("click", (evento) => {
      if (evento.target.closest("a")) alternarMenuMobile(false);
    });

    iniciarUtilitariosMenu();
  }
});
