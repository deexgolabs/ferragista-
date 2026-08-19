function formatarMoedaCaixa(valor) {
  return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

const NOMES_FORMA_PAGAMENTO = {
  dinheiro: "Dinheiro",
  pix: "PIX",
  cartao_debito: "Cartão de débito",
  cartao_credito: "Cartão de crédito",
  fiado: "Fiado",
};

async function carregarCaixaAtual() {
  const sessao = await Api.caixaAtual();

  document.getElementById("bloco-caixa-fechado").classList.toggle("oculto", !!sessao);
  document.getElementById("bloco-caixa-aberto").classList.toggle("oculto", !sessao);

  if (!sessao) return;

  document.getElementById("valor-abertura-atual").textContent = formatarMoedaCaixa(sessao.valor_abertura);
  document.getElementById("valor-total-vendas").textContent = formatarMoedaCaixa(sessao.resumo.total_vendas);
  document.getElementById("valor-suprimentos").textContent = formatarMoedaCaixa(sessao.resumo.suprimentos);
  document.getElementById("valor-sangrias").textContent = formatarMoedaCaixa(sessao.resumo.sangrias);
  document.getElementById("valor-esperado-dinheiro").textContent = formatarMoedaCaixa(sessao.resumo.valor_esperado_dinheiro);

  const porForma = sessao.resumo.vendas_por_forma_pagamento;
  document.getElementById("tabela-vendas-forma").innerHTML =
    Object.entries(porForma)
      .map(([forma, total]) => `<tr><td>${NOMES_FORMA_PAGAMENTO[forma] || forma}</td><td>${formatarMoedaCaixa(total)}</td></tr>`)
      .join("") || "<tr><td colspan='2'>Nenhuma venda nesta sessão ainda.</td></tr>";

  await carregarMovimentacoesCaixa();
}

async function carregarMovimentacoesCaixa() {
  const movimentacoes = await Api.listarMovimentacoesCaixa();
  document.getElementById("tabela-movimentacoes-caixa").innerHTML =
    movimentacoes
      .map(
        (m) => `
          <tr>
            <td>${new Date(m.criado_em).toLocaleString("pt-BR")}</td>
            <td><span class="selo ${m.tipo === "suprimento" ? "selo-ativo" : "selo-inativo"}">${m.tipo}</span></td>
            <td>${formatarMoedaCaixa(m.valor)}</td>
            <td>${m.motivo || "—"}</td>
            <td>${m.usuario_nome || "—"}</td>
          </tr>
        `
      )
      .join("") || "<tr><td colspan='5'>Nenhuma movimentação registrada nesta sessão.</td></tr>";
}

async function carregarSessoesCaixa() {
  const sessoes = await Api.listarSessoesCaixa();
  document.getElementById("tabela-sessoes-caixa").innerHTML =
    sessoes
      .map(
        (s) => `
          <tr>
            <td>${new Date(s.aberto_em).toLocaleString("pt-BR")}</td>
            <td>${s.fechado_em ? new Date(s.fechado_em).toLocaleString("pt-BR") : "—"}</td>
            <td>${formatarMoedaCaixa(s.valor_abertura)}</td>
            <td>${s.valor_fechamento_informado !== null ? formatarMoedaCaixa(s.valor_fechamento_informado) : "—"}</td>
            <td><span class="selo ${s.status === "aberto" ? "selo-ativo" : "selo-info"}">${s.status}</span></td>
          </tr>
        `
      )
      .join("") || "<tr><td colspan='5'>Nenhuma sessão de caixa registrada ainda.</td></tr>";
}

document.getElementById("btn-abrir-caixa").addEventListener("click", async () => {
  await Api.abrirCaixa(document.getElementById("valor-abertura").value || 0);
  await carregarCaixaAtual();
  await carregarSessoesCaixa();
});

document.getElementById("btn-registrar-movimentacao-caixa").addEventListener("click", async () => {
  const valor = document.getElementById("movimentacao-caixa-valor").value;
  if (!valor || Number(valor) <= 0) {
    alert("Informe um valor maior que zero.");
    return;
  }
  try {
    await Api.criarMovimentacaoCaixa({
      tipo: document.getElementById("movimentacao-caixa-tipo").value,
      valor,
      motivo: document.getElementById("movimentacao-caixa-motivo").value,
    });
    document.getElementById("movimentacao-caixa-valor").value = "";
    document.getElementById("movimentacao-caixa-motivo").value = "";
    await carregarCaixaAtual();
  } catch (erro) {
    alert(erro.message);
  }
});

document.getElementById("btn-fechar-caixa").addEventListener("click", async () => {
  if (!confirm("Fechar o caixa? Isso encerra a sessão atual.")) return;
  await Api.fecharCaixa({
    valor_fechamento_informado: document.getElementById("valor-fechamento").value || null,
    observacoes: document.getElementById("fechamento-observacoes").value,
  });
  await carregarCaixaAtual();
  await carregarSessoesCaixa();
});

document.addEventListener("DOMContentLoaded", async () => {
  await carregarCaixaAtual();
  await carregarSessoesCaixa();
});
