(function aplicarTemaSalvo() {
  var tema = localStorage.getItem("tema") || "claro";
  document.documentElement.setAttribute("data-tema", tema);
})();

function alternarTema() {
  var atual = document.documentElement.getAttribute("data-tema") || "claro";
  var novo = atual === "escuro" ? "claro" : "escuro";
  document.documentElement.setAttribute("data-tema", novo);
  localStorage.setItem("tema", novo);
  var botao = document.getElementById("btn-alternar-tema");
  if (botao) botao.innerHTML = svgIcone(novo === "escuro" ? "sun" : "moon");
}
