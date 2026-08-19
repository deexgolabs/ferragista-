const dialogCompra = document.getElementById("dialog-compra");
const formCompra = document.getElementById("form-compra");
const dialogReceberCompra = document.getElementById("dialog-receber-compra");

let comprasCache = [];
let produtosParaCompra = [];
let itensCompraAtual = []; // [{produto_id, nome, quantidade, preco_unitario}]
let compraIdParaReceber = null;

function formatarMoeda4(valor) {
  return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

async function carregarFornecedoresSelect() {
  const fornecedores = await Api.listarFornecedores();
  document.getElementById("compra-fornecedor").innerHTML =
    '<option value="">Sem fornecedor definido</option>' +
    fornecedores.map((f) => `<option value="${f.id}">${f.nome}</option>`).join("");
}

async function carregarProdutosParaCompra() {
  produtosParaCompra = await Api.listarProdutos("?ativo=true");
  document.getElementById("compra-item-produto").innerHTML = produtosParaCompra
    .map((p) => `<option value="${p.id}">${p.nome}</option>`)
    .join("");
}

function renderizarItensCompra() {
  const total = itensCompraAtual.reduce((soma, item) => soma + item.quantidade * item.preco_unitario, 0);
  document.getElementById("lista-itens-compra").innerHTML =
    itensCompraAtual
      .map(
        (item, indice) => `
          <div class="pdv-carrinho-item">
            <div style="flex: 1;">${item.nome}</div>
            <span>${item.quantidade} x ${formatarMoeda4(item.preco_unitario)}</span>
            <strong>${formatarMoeda4(item.quantidade * item.preco_unitario)}</strong>
            <button type="button" class="btn btn-perigo" style="padding: 0.4rem 0.6rem;" onclick="removerItemCompra(${indice})">${svgIcone("trash")}</button>
          </div>
        `
      )
      .join("") || '<p class="texto-suave-pequeno">Nenhum item adicionado.</p>';
  document.getElementById("compra-total-valor").textContent = formatarMoeda4(total);
}

function removerItemCompra(indice) {
  itensCompraAtual.splice(indice, 1);
  renderizarItensCompra();
}

document.getElementById("btn-add-item-compra").addEventListener("click", () => {
  const produtoId = Number(document.getElementById("compra-item-produto").value);
  const produto = produtosParaCompra.find((p) => p.id === produtoId);
  const quantidade = Number(document.getElementById("compra-item-quantidade").value || 0);
  const preco = Number(document.getElementById("compra-item-preco").value || produto?.preco_custo || 0);

  if (!produto || quantidade <= 0) return;

  itensCompraAtual.push({ produto_id: produto.id, nome: produto.nome, quantidade, preco_unitario: preco });
  renderizarItensCompra();
  document.getElementById("compra-item-quantidade").value = 1;
  document.getElementById("compra-item-preco").value = "";
});

async function carregarCompras() {
  comprasCache = await Api.listarCompras();
  document.getElementById("tabela-compras").innerHTML =
    comprasCache
      .map(
        (c) => `
          <tr>
            <td>${new Date(c.data_pedido).toLocaleDateString("pt-BR")}</td>
            <td>${c.fornecedor_nome || "—"}</td>
            <td>${c.itens.length} item(ns)</td>
            <td>${formatarMoeda4(c.total)}</td>
            <td><span class="selo ${c.status === "recebida" ? "selo-recebida" : c.status === "cancelada" ? "selo-cancelada" : "selo-pendente"}">${c.status}</span></td>
            <td>
              ${c.status === "pendente" ? `<button class="btn btn-secundario" onclick="abrirReceberCompra(${c.id})">Receber</button>
              <button class="btn btn-perigo" onclick="cancelarCompra(${c.id})">Cancelar</button>` : ""}
            </td>
          </tr>
        `
      )
      .join("") || "<tr><td colspan='6'>Nenhum pedido de compra registrado.</td></tr>";
}

function abrirReceberCompra(id) {
  compraIdParaReceber = id;
  document.getElementById("receber-compra-vencimento").value = "";
  dialogReceberCompra.showModal();
}

document.getElementById("btn-confirmar-recebimento").addEventListener("click", async () => {
  await Api.receberCompra(compraIdParaReceber, { vencimento: document.getElementById("receber-compra-vencimento").value || null });
  dialogReceberCompra.close();
  carregarCompras();
});
document.getElementById("btn-cancelar-receber-compra").addEventListener("click", () => dialogReceberCompra.close());

async function cancelarCompra(id) {
  if (!confirm("Cancelar este pedido de compra?")) return;
  await Api.cancelarCompra(id);
  carregarCompras();
}

document.getElementById("btn-nova-compra").addEventListener("click", async () => {
  formCompra.reset();
  itensCompraAtual = [];
  renderizarItensCompra();
  await carregarFornecedoresSelect();
  await carregarProdutosParaCompra();
  dialogCompra.showModal();
});
document.getElementById("btn-cancelar-compra").addEventListener("click", () => dialogCompra.close());

formCompra.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  if (itensCompraAtual.length === 0) {
    alert("Adicione ao menos um item.");
    return;
  }

  await Api.criarCompra({
    fornecedor_id: document.getElementById("compra-fornecedor").value || null,
    observacoes: document.getElementById("compra-observacoes").value,
    itens: itensCompraAtual.map((item) => ({
      produto_id: item.produto_id,
      quantidade: item.quantidade,
      preco_unitario: item.preco_unitario,
    })),
  });

  dialogCompra.close();
  carregarCompras();
});

document.addEventListener("DOMContentLoaded", carregarCompras);
