function formatarMoeda6(valor) {
  return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

async function carregarRelatorios() {
  const maisVendidos = await Api.produtosMaisVendidos(30);
  document.getElementById("tabela-mais-vendidos").innerHTML =
    maisVendidos
      .map((item) => `<tr><td>${item.produto_nome}</td><td>${item.quantidade_total}</td><td>${formatarMoeda6(item.valor_total)}</td></tr>`)
      .join("") || "<tr><td colspan='3'>Sem dados no período.</td></tr>";

  const estoqueBaixo = await Api.estoqueBaixo();
  document.getElementById("tabela-estoque-baixo").innerHTML =
    estoqueBaixo
      .map((p) => `<tr><td>${p.nome}</td><td>${p.quantidade_estoque} ${p.unidade}</td><td>${p.estoque_minimo} ${p.unidade}</td></tr>`)
      .join("") || "<tr><td colspan='3'>Nenhum produto com estoque baixo.</td></tr>";

  try {
    const vendasPorPeriodo = await Api.vendasPorPeriodo(30);
    const linhas = Object.entries(vendasPorPeriodo)
      .map(([data, total]) => `<tr><td>${new Date(data + "T00:00:00").toLocaleDateString("pt-BR")}</td><td>${formatarMoeda6(total)}</td></tr>`)
      .join("");
    document.getElementById("tabela-vendas-periodo").innerHTML = linhas || "<tr><td colspan='2'>Sem vendas no período.</td></tr>";

    const curvaAbc = await Api.curvaAbc(30);
    document.getElementById("tabela-curva-abc").innerHTML =
      curvaAbc
        .map(
          (item) => `
            <tr>
              <td>${item.produto_nome}</td>
              <td>${formatarMoeda6(item.valor_total)}</td>
              <td>${item.percentual_do_total}%</td>
              <td><span class="selo ${item.classe === "A" ? "selo-ativo" : item.classe === "B" ? "selo-pendente" : "selo-inativo"}">${item.classe}</span></td>
            </tr>
          `
        )
        .join("") || "<tr><td colspan='4'>Sem vendas no período.</td></tr>";

    const margem = await Api.margem(30);
    document.getElementById("valor-margem-total").textContent = formatarMoeda6(margem.margem_total);
    document.getElementById("texto-margem-percentual").textContent =
      `Receita ${formatarMoeda6(margem.receita_total)} — Custo ${formatarMoeda6(margem.custo_total)} — ${margem.margem_percentual}% de margem`;
    document.getElementById("tabela-margem-produto").innerHTML =
      margem.por_produto
        .map((item) => `<tr><td>${item.produto_nome}</td><td>${formatarMoeda6(item.margem)}</td><td>${item.margem_percentual}%</td></tr>`)
        .join("") || "<tr><td colspan='3'>Sem vendas no período.</td></tr>";

    const comissoes = await Api.comissoes(30);
    document.getElementById("tabela-comissoes").innerHTML =
      comissoes
        .map(
          (item) => `<tr><td>${item.usuario_nome}</td><td>${formatarMoeda6(item.total_vendido)}</td><td>${item.percentual_comissao}%</td><td>${formatarMoeda6(item.comissao_devida)}</td></tr>`
        )
        .join("") || "<tr><td colspan='4'>Nenhuma venda com vendedor identificado no período.</td></tr>";
  } catch {
    document.getElementById("tabela-vendas-periodo").innerHTML = "<tr><td colspan='2'>Disponível apenas para admin/gerente.</td></tr>";
  }
}

document.addEventListener("DOMContentLoaded", carregarRelatorios);
