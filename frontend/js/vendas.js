let produtosDisponiveis = [];
let carrinho = []; // [{produto_id, nome, unidade, preco_unitario, quantidade, estoque_disponivel}]

function formatarMoeda3(valor) {
  return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function calcularTotalCarrinho() {
  const subtotal = carrinho.reduce((soma, item) => soma + item.quantidade * item.preco_unitario, 0);
  const desconto = Number(document.getElementById("pdv-desconto").value || 0);
  return Math.max(0, subtotal - desconto);
}

function renderizarCarrinho() {
  const lista = document.getElementById("lista-carrinho");
  const vazio = document.getElementById("carrinho-vazio");

  if (carrinho.length === 0) {
    vazio.classList.remove("oculto");
    lista.innerHTML = "";
  } else {
    vazio.classList.add("oculto");
    lista.innerHTML = carrinho
      .map(
        (item, indice) => `
          <div class="pdv-carrinho-item">
            <div style="flex: 1;">
              <strong>${item.nome}</strong><br />
              <span class="texto-suave-pequeno">${formatarMoeda3(item.preco_unitario)} / ${item.unidade}</span>
            </div>
            <input type="number" class="pdv-carrinho-qtd" step="0.001" min="0.001" value="${item.quantidade}"
              onchange="atualizarQuantidadeCarrinho(${indice}, this.value)" />
            <strong>${formatarMoeda3(item.quantidade * item.preco_unitario)}</strong>
            <button type="button" class="btn btn-perigo" style="padding: 0.4rem 0.6rem;" onclick="removerDoCarrinho(${indice})">${svgIcone("trash")}</button>
          </div>
        `
      )
      .join("");
  }

  document.getElementById("pdv-total-valor").textContent = formatarMoeda3(calcularTotalCarrinho());
}

function atualizarQuantidadeCarrinho(indice, valor) {
  const quantidade = Number(valor);
  if (quantidade <= 0) {
    carrinho.splice(indice, 1);
  } else {
    carrinho[indice].quantidade = quantidade;
  }
  renderizarCarrinho();
}

function removerDoCarrinho(indice) {
  carrinho.splice(indice, 1);
  renderizarCarrinho();
}

function adicionarAoCarrinho(produto) {
  const existente = carrinho.find((item) => item.produto_id === produto.id);
  if (existente) {
    existente.quantidade += 1;
  } else {
    carrinho.push({
      produto_id: produto.id,
      nome: produto.nome,
      unidade: produto.unidade,
      preco_unitario: produto.preco_venda,
      quantidade: 1,
      estoque_disponivel: produto.quantidade_estoque,
    });
  }
  renderizarCarrinho();
  document.getElementById("busca-produto-pdv").value = "";
  document.getElementById("resultados-busca-produto").classList.add("oculto");
}

async function buscarProdutosPdv() {
  const termo = document.getElementById("busca-produto-pdv").value.trim();
  const resultadosEl = document.getElementById("resultados-busca-produto");
  if (termo.length < 1) {
    resultadosEl.classList.add("oculto");
    return;
  }

  const produtos = await Api.listarProdutos(`?busca=${encodeURIComponent(termo)}&ativo=true`);
  if (produtos.length === 0) {
    resultadosEl.innerHTML = '<div class="resultado-produto-item">Nenhum produto encontrado.</div>';
  } else {
    resultadosEl.innerHTML = produtos
      .map(
        (p) => `
          <div class="resultado-produto-item" onclick='adicionarAoCarrinho(${JSON.stringify(p).replace(/'/g, "&apos;")})'>
            <strong>${p.nome}</strong> — ${formatarMoeda3(p.preco_venda)} <span class="texto-suave-pequeno">(${p.quantidade_estoque} ${p.unidade} em estoque)</span>
          </div>
        `
      )
      .join("");
  }
  resultadosEl.classList.remove("oculto");
}

async function carregarClientesPdv() {
  const clientes = await Api.listarClientes();
  document.getElementById("pdv-cliente").innerHTML =
    '<option value="">Cliente não identificado</option>' +
    clientes.map((c) => `<option value="${c.id}">${c.nome}</option>`).join("");
}

async function finalizarVenda() {
  const erroEl = document.getElementById("erro-pdv");
  erroEl.classList.add("oculto");

  if (carrinho.length === 0) {
    erroEl.textContent = "Adicione ao menos um item ao carrinho.";
    erroEl.classList.remove("oculto");
    return;
  }

  const dados = {
    cliente_id: document.getElementById("pdv-cliente").value || null,
    forma_pagamento: document.getElementById("pdv-forma-pagamento").value,
    desconto: document.getElementById("pdv-desconto").value || 0,
    itens: carrinho.map((item) => ({
      produto_id: item.produto_id,
      quantidade: item.quantidade,
      preco_unitario: item.preco_unitario,
    })),
  };

  try {
    const venda = await Api.criarVenda(dados);
    carrinho = [];
    renderizarCarrinho();
    document.getElementById("pdv-desconto").value = 0;
    document.getElementById("pdv-cliente").value = "";
    carregarVendas();
    window.open(`recibo-venda.html?id=${venda.id}`, "_blank");
    document.getElementById("codigo-barras-pdv").focus();
  } catch (erro) {
    erroEl.textContent = erro.message;
    erroEl.classList.remove("oculto");
  }
}

async function carregarVendas() {
  const vendas = await Api.listarVendas();
  document.getElementById("tabela-vendas").innerHTML =
    vendas
      .map(
        (v) => `
          <tr>
            <td>${new Date(v.criado_em).toLocaleString("pt-BR")}</td>
            <td>${v.cliente_nome || "—"}</td>
            <td>${v.forma_pagamento.replace("_", " ")}</td>
            <td>${formatarMoeda3(v.total)}</td>
            <td><span class="selo ${v.status === "concluida" ? "selo-concluida" : "selo-cancelada"}">${v.status}</span></td>
            <td>
              <a class="btn btn-secundario" href="recibo-venda.html?id=${v.id}" target="_blank" rel="noopener">Recibo</a>
              ${v.status === "concluida" ? `<button class="btn btn-perigo" onclick="cancelarVenda(${v.id})">Cancelar</button>` : ""}
            </td>
          </tr>
        `
      )
      .join("") || "<tr><td colspan='6'>Nenhuma venda registrada ainda.</td></tr>";
}

async function cancelarVenda(id) {
  if (!confirm("Cancelar esta venda? O estoque será estornado.")) return;
  await Api.cancelarVenda(id);
  carregarVendas();
}

async function adicionarPorCodigoBarras() {
  const campo = document.getElementById("codigo-barras-pdv");
  const codigo = campo.value.trim();
  const erroEl = document.getElementById("erro-codigo-barras");
  erroEl.classList.add("oculto");
  if (!codigo) return;

  const produtos = await Api.listarProdutos(`?busca=${encodeURIComponent(codigo)}&ativo=true`);
  const encontrado = produtos.find((p) => (p.codigo || "").toLowerCase() === codigo.toLowerCase());

  if (!encontrado) {
    erroEl.textContent = `Nenhum produto com o código "${codigo}".`;
    erroEl.classList.remove("oculto");
  } else if (encontrado.quantidade_estoque <= 0) {
    erroEl.textContent = `${encontrado.nome} está sem estoque.`;
    erroEl.classList.remove("oculto");
  } else {
    adicionarAoCarrinho(encontrado);
  }

  campo.value = "";
  campo.focus();
}

document.getElementById("codigo-barras-pdv").addEventListener("keydown", (evento) => {
  if (evento.key === "Enter") {
    evento.preventDefault();
    adicionarPorCodigoBarras();
  }
});

document.getElementById("busca-produto-pdv").addEventListener("input", buscarProdutosPdv);
document.getElementById("pdv-desconto").addEventListener("input", renderizarCarrinho);
document.getElementById("btn-finalizar-venda").addEventListener("click", finalizarVenda);

document.addEventListener("click", (evento) => {
  const wrapper = document.querySelector(".campo-busca-wrapper");
  if (!wrapper.contains(evento.target)) {
    document.getElementById("resultados-busca-produto").classList.add("oculto");
  }
});

document.addEventListener("DOMContentLoaded", async () => {
  await carregarClientesPdv();
  await carregarVendas();
  document.getElementById("codigo-barras-pdv").focus();
});
