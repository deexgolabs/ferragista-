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

function montarBarraLateralCentral(paginaAtiva) {
  const usuario = obterUsuarioLogado();

  const links = [
    { href: "central-dashboard.html", texto: "Painel", chave: "central-dashboard", icone: "home" },
    { href: "central-lojas.html", texto: "Lojas", chave: "central-lojas", icone: "grid" },
  ];

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
    <aside class="barra-lateral" id="barra-lateral-menu">
      <div class="marca">
        <div class="marca-icone">${svgIcone("wrench")}</div>
        <div class="marca-texto">
          <strong>Ferragista+</strong>
          <span>Painel do dono</span>
        </div>
      </div>

      <nav class="menu-nav">
        <div class="menu-grupo">
          <span class="menu-grupo-titulo">Plataforma</span>
          ${itens}
        </div>
      </nav>

      <div class="rodape-menu">
        <div class="utilitarios-menu">
          <button type="button" class="btn-icone" id="btn-alternar-tema" aria-label="Alternar tema">${svgIcone("moon")}</button>
        </div>
        <div class="usuario-info">
          <div class="avatar">${iniciaisUsuario(usuario.nome)}</div>
          <div class="usuario-textos">
            <strong>${usuario.nome || "Dono"}</strong>
            <span>super admin</span>
          </div>
        </div>
        <a href="#" onclick="sair(); return false;" class="item-menu">
          <span class="item-menu-icone">${svgIcone("logOut")}</span>Sair
        </a>
      </div>
    </aside>
  `;
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
    alvo.outerHTML = montarBarraLateralCentral(alvo.dataset.pagina);

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

    const botaoTema = document.getElementById("btn-alternar-tema");
    if (botaoTema) {
      botaoTema.innerHTML = svgIcone((document.documentElement.getAttribute("data-tema") || "claro") === "escuro" ? "sun" : "moon");
      botaoTema.addEventListener("click", alternarTema);
    }
  }
});
