async function carregarCentralDashboard() {
  const metricas = await Api.metricasCentral();
  document.getElementById("valor-total-lojas").textContent = metricas.total_lojas;
  document.getElementById("valor-trial").textContent = metricas.trial;
  document.getElementById("valor-ativas").textContent = metricas.ativa;
  document.getElementById("valor-suspensas").textContent = metricas.suspensa + metricas.cancelada;

  const analytics = await Api.analyticsCentral();
  document.getElementById("tabela-top-lojas").innerHTML =
    analytics.top_lojas_por_vendas
      .map((item) => `<tr><td>${item.nome}</td><td>${item.total}</td></tr>`)
      .join("") || "<tr><td colspan='2'>Nenhuma venda registrada ainda.</td></tr>";
}

document.addEventListener("DOMContentLoaded", carregarCentralDashboard);
