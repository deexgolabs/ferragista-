// Service worker do Ferragista+ — cacheia o "app shell" (CSS/JS/ícones e a
// tela de login) pra abrir rápido e funcionar offline em telas já visitadas.
// Nunca cacheia /api/* — dados de loja/estoque/financeiro sempre vêm da rede.

const CACHE_NAME = "ferragista-v1";

const ASSETS_ESSENCIAIS = [
  "/pages/login.html",
  "/css/style.css",
  "/js/api.js",
  "/js/auth.js",
  "/js/icones.js",
  "/js/tema.js",
  "/js/layout.js",
  "/js/pwa.js",
  "/manifest.json",
  "/assets/img/icon-192.png",
  "/assets/img/icon-512.png",
];

self.addEventListener("install", (evento) => {
  evento.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(ASSETS_ESSENCIAIS))
      .catch(() => {})
  );
  self.skipWaiting();
});

self.addEventListener("activate", (evento) => {
  evento.waitUntil(
    caches
      .keys()
      .then((chaves) => Promise.all(chaves.filter((chave) => chave !== CACHE_NAME).map((chave) => caches.delete(chave))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (evento) => {
  const url = new URL(evento.request.url);

  // API sempre vai na rede — nunca serve dado antigo/de outra sessão.
  if (url.pathname.startsWith("/api/") || evento.request.method !== "GET") {
    return;
  }

  evento.respondWith(
    caches.match(evento.request).then((respostaCache) => {
      const buscaRede = fetch(evento.request)
        .then((respostaRede) => {
          if (respostaRede && respostaRede.ok) {
            const clone = respostaRede.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(evento.request, clone));
          }
          return respostaRede;
        })
        .catch(() => {
          if (evento.request.mode === "navigate") {
            return caches.match("/pages/login.html");
          }
          return undefined;
        });

      return respostaCache || buscaRede;
    })
  );
});
