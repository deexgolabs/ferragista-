if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => {
      // offline no primeiro acesso, ou navegador sem suporte — sem problema,
      // o app continua funcionando normalmente, só sem o cache offline
    });
  });
}

function estaRodandoInstalado() {
  return window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true;
}

let eventoInstalacaoAdiado = null;

window.addEventListener("beforeinstallprompt", (evento) => {
  evento.preventDefault();
  eventoInstalacaoAdiado = evento;
  mostrarBotaoInstalar();
});

window.addEventListener("appinstalled", () => {
  eventoInstalacaoAdiado = null;
  esconderBotaoInstalar();
});

function mostrarBotaoInstalar() {
  if (estaRodandoInstalado() || document.getElementById("btn-instalar-pwa")) return;

  const botao = document.createElement("button");
  botao.id = "btn-instalar-pwa";
  botao.type = "button";
  botao.className = "btn-instalar-pwa";
  botao.innerHTML = "⬇ Instalar app";
  botao.addEventListener("click", async () => {
    if (!eventoInstalacaoAdiado) return;
    botao.disabled = true;
    eventoInstalacaoAdiado.prompt();
    await eventoInstalacaoAdiado.userChoice;
    eventoInstalacaoAdiado = null;
    esconderBotaoInstalar();
  });
  document.body.appendChild(botao);
}

function esconderBotaoInstalar() {
  const botao = document.getElementById("btn-instalar-pwa");
  if (botao) botao.remove();
}

document.addEventListener("DOMContentLoaded", () => {
  if (estaRodandoInstalado()) {
    document.documentElement.classList.add("pwa-instalado");
  }
});
