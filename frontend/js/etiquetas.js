let produtosComCodigoCache = [];

function formatarMoedaEtiqueta(valor) {
  return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

async function carregarProdutosParaSelecao() {
  const busca = document.getElementById("busca-produto-etiqueta").value.trim();
  const todos = await Api.listarProdutos(`?ativo=true${busca ? `&busca=${encodeURIComponent(busca)}` : ""}`);
  produtosComCodigoCache = todos.filter((p) => p.codigo);

  document.getElementById("tabela-selecao-produtos").innerHTML =
    produtosComCodigoCache
      .map(
        (p) => `
          <tr>
            <td><input type="checkbox" class="check-etiqueta" data-id="${p.id}" /></td>
            <td>${p.nome}</td>
            <td>${p.codigo}</td>
            <td>${formatarMoedaEtiqueta(p.preco_venda)}</td>
            <td><input type="number" min="1" value="1" class="qtd-etiqueta" data-id="${p.id}" style="width: 60px;" /></td>
          </tr>
        `
      )
      .join("") || "<tr><td colspan='5'>Nenhum produto com código cadastrado encontrado.</td></tr>";
}

async function gerarEtiquetas() {
  const selecionados = Array.from(document.querySelectorAll(".check-etiqueta:checked")).map((el) => Number(el.dataset.id));
  if (selecionados.length === 0) {
    alert("Selecione ao menos um produto.");
    return;
  }

  const grade = document.getElementById("grade-etiquetas");
  grade.innerHTML = "<p>Gerando etiquetas...</p>";

  const blocos = [];
  for (const produtoId of selecionados) {
    const produto = produtosComCodigoCache.find((p) => p.id === produtoId);
    const quantidadeInput = document.querySelector(`.qtd-etiqueta[data-id="${produtoId}"]`);
    const copias = Math.max(1, Number(quantidadeInput.value || 1));
    const urlImagem = await Api.urlCodigoBarrasProduto(produtoId);

    for (let i = 0; i < copias; i++) {
      blocos.push(`
        <div class="etiqueta">
          <div class="nome">${produto.nome}</div>
          <div class="preco">${formatarMoedaEtiqueta(produto.preco_venda)}</div>
          <img src="${urlImagem}" alt="Código de barras ${produto.codigo}" />
        </div>
      `);
    }
  }

  grade.innerHTML = blocos.join("");
}

document.getElementById("busca-produto-etiqueta").addEventListener("input", carregarProdutosParaSelecao);
document.getElementById("btn-gerar-etiquetas").addEventListener("click", gerarEtiquetas);
document.getElementById("btn-imprimir-etiquetas").addEventListener("click", () => window.print());

document.addEventListener("DOMContentLoaded", carregarProdutosParaSelecao);
