const dialogMovimentacao = document.getElementById("dialog-movimentacao");
const formMovimentacao = document.getElementById("form-movimentacao");

async function carregarProdutosSelect() {
  const produtos = await Api.listarProdutos("?ativo=true");
  document.getElementById("movimentacao-produto").innerHTML = produtos
    .map((p) => `<option value="${p.id}">${p.nome} (${p.quantidade_estoque} ${p.unidade} em estoque)</option>`)
    .join("");
}

async function carregarMovimentacoes() {
  const movimentacoes = await Api.listarMovimentacoes();
  document.getElementById("tabela-movimentacoes").innerHTML =
    movimentacoes
      .map(
        (m) => `
          <tr>
            <td>${new Date(m.criado_em).toLocaleString("pt-BR")}</td>
            <td>${m.produto_nome}</td>
            <td><span class="selo ${m.tipo === "entrada" ? "selo-ativo" : m.tipo === "saida" ? "selo-inativo" : "selo-info"}">${m.tipo}</span></td>
            <td>${m.quantidade}</td>
            <td>${m.motivo || "—"}</td>
          </tr>
        `
      )
      .join("") || "<tr><td colspan='5'>Nenhuma movimentação registrada ainda.</td></tr>";
}

document.getElementById("btn-nova-movimentacao").addEventListener("click", async () => {
  formMovimentacao.reset();
  await carregarProdutosSelect();
  dialogMovimentacao.showModal();
});
document.getElementById("btn-cancelar-movimentacao").addEventListener("click", () => dialogMovimentacao.close());

formMovimentacao.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  try {
    await Api.criarMovimentacao({
      produto_id: document.getElementById("movimentacao-produto").value,
      tipo: document.getElementById("movimentacao-tipo").value,
      quantidade: document.getElementById("movimentacao-quantidade").value,
      motivo: document.getElementById("movimentacao-motivo").value,
    });
    dialogMovimentacao.close();
    formMovimentacao.reset();
    carregarMovimentacoes();
  } catch (erro) {
    alert(erro.message);
  }
});

document.addEventListener("DOMContentLoaded", carregarMovimentacoes);
