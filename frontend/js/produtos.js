const dialogProduto = document.getElementById("dialog-produto");
const formProduto = document.getElementById("form-produto");
const dialogCategoria = document.getElementById("dialog-categoria");
const formCategoria = document.getElementById("form-categoria");

let produtosCache = [];
let categoriasCache = [];

function formatarMoedaOuTraco(valor) {
  return valor !== null && valor !== undefined ? Number(valor).toLocaleString("pt-BR", { style: "currency", currency: "BRL" }) : "—";
}

async function carregarCategorias() {
  categoriasCache = await Api.listarCategorias();
  const opcoes = categoriasCache.map((c) => `<option value="${c.id}">${c.nome}</option>`).join("");

  const selectFiltro = document.getElementById("filtro-categoria");
  selectFiltro.innerHTML = '<option value="">Todas as categorias</option>' + opcoes;

  const selectProduto = document.getElementById("produto-categoria");
  selectProduto.innerHTML = '<option value="">Sem categoria</option>' + opcoes;
}

async function carregarProdutos() {
  const busca = document.getElementById("busca-produto").value.trim();
  const categoriaId = document.getElementById("filtro-categoria").value;
  const estoqueBaixo = document.getElementById("filtro-estoque-baixo").checked;

  const params = new URLSearchParams();
  if (busca) params.set("busca", busca);
  if (categoriaId) params.set("categoria_id", categoriaId);
  if (estoqueBaixo) params.set("estoque_baixo", "true");

  produtosCache = await Api.listarProdutos(`?${params.toString()}`);

  document.getElementById("tabela-produtos").innerHTML =
    produtosCache
      .map(
        (p) => `
          <tr>
            <td>${p.nome}</td>
            <td>${p.codigo || "—"}</td>
            <td>${p.categoria_nome || "—"}</td>
            <td>${formatarMoedaOuTraco(p.preco_custo)}</td>
            <td>${formatarMoedaOuTraco(p.preco_venda)}</td>
            <td>${p.quantidade_estoque} ${p.unidade}${p.estoque_baixo ? ' <span class="selo selo-pendente">baixo</span>' : ""}</td>
            <td>
              <button class="btn btn-secundario" onclick="editarProduto(${p.id})">Editar</button>
              <button class="btn btn-perigo" onclick="removerProduto(${p.id})">Excluir</button>
            </td>
          </tr>
        `
      )
      .join("") || "<tr><td colspan='7'>Nenhum produto encontrado.</td></tr>";
}

function abrirDialogProduto() {
  formProduto.reset();
  document.getElementById("produto-id").value = "";
  document.getElementById("titulo-dialog-produto").textContent = "Novo produto";
  document.getElementById("campo-quantidade-inicial").classList.remove("oculto");
  dialogProduto.showModal();
}

function editarProduto(id) {
  const produto = produtosCache.find((p) => p.id === id);
  if (!produto) return;

  document.getElementById("produto-id").value = produto.id;
  document.getElementById("produto-nome").value = produto.nome;
  document.getElementById("produto-codigo").value = produto.codigo || "";
  document.getElementById("produto-categoria").value = produto.categoria_id || "";
  document.getElementById("produto-unidade").value = produto.unidade;
  document.getElementById("produto-estoque-minimo").value = produto.estoque_minimo;
  document.getElementById("produto-preco-custo").value = produto.preco_custo ?? "";
  document.getElementById("produto-preco-venda").value = produto.preco_venda;
  document.getElementById("titulo-dialog-produto").textContent = "Editar produto";
  document.getElementById("campo-quantidade-inicial").classList.add("oculto");
  dialogProduto.showModal();
}

async function removerProduto(id) {
  if (!confirm("Excluir este produto?")) return;
  await Api.excluirProduto(id);
  carregarProdutos();
}

formProduto.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const id = document.getElementById("produto-id").value;
  const dados = {
    nome: document.getElementById("produto-nome").value,
    codigo: document.getElementById("produto-codigo").value || null,
    categoria_id: document.getElementById("produto-categoria").value || null,
    unidade: document.getElementById("produto-unidade").value,
    estoque_minimo: document.getElementById("produto-estoque-minimo").value || 0,
    preco_custo: document.getElementById("produto-preco-custo").value || null,
    preco_venda: document.getElementById("produto-preco-venda").value,
  };

  if (id) {
    await Api.atualizarProduto(id, dados);
  } else {
    dados.quantidade_estoque = document.getElementById("produto-quantidade").value || 0;
    await Api.criarProduto(dados);
  }

  dialogProduto.close();
  formProduto.reset();
  carregarProdutos();
});

document.getElementById("btn-novo-produto").addEventListener("click", abrirDialogProduto);
document.getElementById("btn-cancelar-produto").addEventListener("click", () => dialogProduto.close());
document.getElementById("busca-produto").addEventListener("input", carregarProdutos);
document.getElementById("filtro-categoria").addEventListener("change", carregarProdutos);
document.getElementById("filtro-estoque-baixo").addEventListener("change", carregarProdutos);

document.getElementById("btn-nova-categoria").addEventListener("click", () => {
  formCategoria.reset();
  dialogCategoria.showModal();
});
document.getElementById("btn-cancelar-categoria").addEventListener("click", () => dialogCategoria.close());
formCategoria.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  await Api.criarCategoria({ nome: document.getElementById("categoria-nome").value });
  dialogCategoria.close();
  formCategoria.reset();
  await carregarCategorias();
  carregarProdutos();
});

document.getElementById("btn-importar-csv").addEventListener("click", () => {
  document.getElementById("input-importar-csv").click();
});

document.getElementById("input-importar-csv").addEventListener("change", async (evento) => {
  const arquivo = evento.target.files[0];
  if (!arquivo) return;

  try {
    const resultado = await Api.importarProdutosCsv(arquivo);
    let mensagem = `${resultado.criados} produto(s) importado(s) com sucesso.`;
    if (resultado.erros.length > 0) {
      mensagem += `\n\nAvisos:\n${resultado.erros.join("\n")}`;
    }
    alert(mensagem);
    await carregarCategorias();
    await carregarProdutos();
  } catch (erro) {
    alert(erro.message);
  } finally {
    evento.target.value = "";
  }
});

document.addEventListener("DOMContentLoaded", async () => {
  await carregarCategorias();
  await carregarProdutos();
});
