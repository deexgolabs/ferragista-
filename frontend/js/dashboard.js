function formatarMoeda(valor) {
  return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

async function carregarDashboard() {
  document.querySelectorAll("[data-icone]").forEach((el) => {
    el.innerHTML = svgIcone(el.dataset.icone);
  });

  const dados = await Api.dashboard();
  document.getElementById("valor-vendas-hoje").textContent = formatarMoeda(dados.vendas_hoje_total);
  document.getElementById("valor-vendas-mes").textContent = formatarMoeda(dados.vendas_mes_total);
  document.getElementById("valor-estoque-baixo").textContent = dados.produtos_estoque_baixo;
  document.getElementById("valor-saldo").textContent = formatarMoeda(dados.saldo_financeiro);
  document.getElementById("valor-a-receber").textContent = formatarMoeda(dados.a_receber);
  document.getElementById("valor-a-pagar").textContent = formatarMoeda(dados.a_pagar);

  const maisVendidos = await Api.produtosMaisVendidos(30);
  document.getElementById("tabela-mais-vendidos").innerHTML =
    maisVendidos
      .map(
        (item) => `
          <tr>
            <td>${item.produto_nome}</td>
            <td>${item.quantidade_total}</td>
            <td>${formatarMoeda(item.valor_total)}</td>
          </tr>
        `
      )
      .join("") || "<tr><td colspan='3'>Nenhuma venda registrada nos últimos 30 dias.</td></tr>";
}

document.addEventListener("DOMContentLoaded", carregarDashboard);
