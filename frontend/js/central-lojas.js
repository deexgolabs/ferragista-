const dialogLoja = document.getElementById("dialog-loja");
const formLoja = document.getElementById("form-loja");
let lojasCache = [];

function seloStatus(status) {
  const classe = status === "ativa" ? "selo-ativo" : status === "trial" ? "selo-info" : "selo-inativo";
  return `<span class="selo ${classe}">${status}</span>`;
}

async function carregarLojas() {
  lojasCache = await Api.listarLojasCentral();
  document.getElementById("tabela-lojas").innerHTML =
    lojasCache
      .map(
        (l) => `
          <tr>
            <td>${l.nome}</td>
            <td>${l.email_contato || "—"}</td>
            <td style="text-transform: capitalize;">${l.plano}</td>
            <td>${seloStatus(l.status)}</td>
            <td>${l.trial_expira_em ? new Date(l.trial_expira_em + "T00:00:00").toLocaleDateString("pt-BR") : "—"}</td>
            <td>${l.total_produtos}</td>
            <td>${l.total_usuarios}</td>
            <td><button class="btn btn-secundario" onclick="editarLoja(${l.id})">Editar</button></td>
          </tr>
        `
      )
      .join("") || "<tr><td colspan='8'>Nenhuma loja cadastrada ainda.</td></tr>";
}

function editarLoja(id) {
  const loja = lojasCache.find((l) => l.id === id);
  if (!loja) return;

  document.getElementById("loja-id").value = loja.id;
  document.getElementById("loja-plano").value = loja.plano;
  document.getElementById("loja-status").value = loja.status;
  document.getElementById("loja-trial-expira").value = loja.trial_expira_em || "";
  dialogLoja.showModal();
}

document.getElementById("btn-cancelar-loja").addEventListener("click", () => dialogLoja.close());

formLoja.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const id = document.getElementById("loja-id").value;
  await Api.atualizarLojaCentral(id, {
    plano: document.getElementById("loja-plano").value,
    status: document.getElementById("loja-status").value,
    trial_expira_em: document.getElementById("loja-trial-expira").value || null,
  });
  dialogLoja.close();
  carregarLojas();
});

document.addEventListener("DOMContentLoaded", carregarLojas);
