const dialogLancamento = document.getElementById("dialog-lancamento");
const formLancamento = document.getElementById("form-lancamento");

function formatarMoeda5(valor) {
  return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

async function carregarResumo() {
  const resumo = await Api.resumoFinanceiro();
  document.getElementById("resumo-entradas").textContent = formatarMoeda5(resumo.entradas);
  document.getElementById("resumo-saidas").textContent = formatarMoeda5(resumo.saidas);
  document.getElementById("resumo-saldo").textContent = formatarMoeda5(resumo.saldo);
  document.getElementById("resumo-pendentes").innerHTML =
    `${formatarMoeda5(resumo.a_receber)} <span class="texto-suave-pequeno">receber</span><br />${formatarMoeda5(resumo.a_pagar)} <span class="texto-suave-pequeno">pagar</span>`;
}

async function carregarLancamentos() {
  const tipo = document.getElementById("filtro-tipo").value;
  const status = document.getElementById("filtro-status").value;
  const params = new URLSearchParams();
  if (tipo) params.set("tipo", tipo);
  if (status) params.set("status", status);

  const lancamentos = await Api.listarLancamentos(`?${params.toString()}`);
  document.getElementById("tabela-lancamentos").innerHTML =
    lancamentos
      .map(
        (l) => `
          <tr>
            <td>${new Date(l.data + "T00:00:00").toLocaleDateString("pt-BR")}</td>
            <td><span class="selo ${l.tipo === "entrada" ? "selo-ativo" : "selo-inativo"}">${l.tipo}</span></td>
            <td>${l.categoria}</td>
            <td>${l.descricao || "—"}</td>
            <td>${formatarMoeda5(l.valor)}</td>
            <td><span class="selo ${l.status === "pago" ? "selo-pago" : "selo-pendente"}">${l.status}</span></td>
            <td>
              ${l.status === "pendente" ? `<button class="btn btn-secundario" onclick="quitarLancamento(${l.id})">Quitar</button>` : ""}
              ${l.origem === "manual" ? `<button class="btn btn-perigo" onclick="excluirLancamento(${l.id})">Excluir</button>` : ""}
            </td>
          </tr>
        `
      )
      .join("") || "<tr><td colspan='7'>Nenhum lançamento encontrado.</td></tr>";
}

async function quitarLancamento(id) {
  await Api.quitarLancamento(id);
  carregarLancamentos();
  carregarResumo();
}

async function excluirLancamento(id) {
  if (!confirm("Excluir este lançamento?")) return;
  await Api.excluirLancamento(id);
  carregarLancamentos();
  carregarResumo();
}

document.getElementById("btn-novo-lancamento").addEventListener("click", () => {
  formLancamento.reset();
  document.getElementById("lancamento-data").value = new Date().toISOString().slice(0, 10);
  dialogLancamento.showModal();
});
document.getElementById("btn-cancelar-lancamento").addEventListener("click", () => dialogLancamento.close());

formLancamento.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  await Api.criarLancamento({
    tipo: document.getElementById("lancamento-tipo").value,
    valor: document.getElementById("lancamento-valor").value,
    categoria: document.getElementById("lancamento-categoria").value || "outros",
    descricao: document.getElementById("lancamento-descricao").value,
    data: document.getElementById("lancamento-data").value,
    status: document.getElementById("lancamento-status").value,
    vencimento: document.getElementById("lancamento-vencimento").value || null,
  });
  dialogLancamento.close();
  formLancamento.reset();
  carregarLancamentos();
  carregarResumo();
});

document.getElementById("filtro-tipo").addEventListener("change", carregarLancamentos);
document.getElementById("filtro-status").addEventListener("change", carregarLancamentos);

document.addEventListener("DOMContentLoaded", async () => {
  await carregarResumo();
  await carregarLancamentos();
});
