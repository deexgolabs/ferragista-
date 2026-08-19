const dialogCliente = document.getElementById("dialog-cliente");
const formCliente = document.getElementById("form-cliente");
let clientesCache = [];

function formatarMoeda2(valor) {
  return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

async function carregarClientes() {
  const busca = document.getElementById("busca-cliente").value.trim();
  clientesCache = await Api.listarClientes(busca ? `?busca=${encodeURIComponent(busca)}` : "");

  document.getElementById("tabela-clientes").innerHTML =
    clientesCache
      .map(
        (c) => `
          <tr>
            <td>${c.nome}</td>
            <td>${c.telefone || "—"}</td>
            <td>${formatarMoeda2(c.limite_fiado)}</td>
            <td>${c.saldo_devedor > 0 ? `<span class="selo selo-pendente">${formatarMoeda2(c.saldo_devedor)}</span>` : formatarMoeda2(0)}</td>
            <td>
              <button class="btn btn-secundario" onclick="editarCliente(${c.id})">Editar</button>
              <button class="btn btn-perigo" onclick="removerCliente(${c.id})">Excluir</button>
            </td>
          </tr>
        `
      )
      .join("") || "<tr><td colspan='5'>Nenhum cliente cadastrado.</td></tr>";
}

function abrirDialogCliente() {
  formCliente.reset();
  document.getElementById("cliente-id").value = "";
  document.getElementById("titulo-dialog-cliente").textContent = "Novo cliente";
  dialogCliente.showModal();
}

function editarCliente(id) {
  const cliente = clientesCache.find((c) => c.id === id);
  if (!cliente) return;

  document.getElementById("cliente-id").value = cliente.id;
  document.getElementById("cliente-nome").value = cliente.nome;
  document.getElementById("cliente-cpf-cnpj").value = cliente.cpf_cnpj || "";
  document.getElementById("cliente-telefone").value = cliente.telefone || "";
  document.getElementById("cliente-email").value = cliente.email || "";
  document.getElementById("cliente-endereco").value = cliente.endereco || "";
  document.getElementById("cliente-limite-fiado").value = cliente.limite_fiado;
  document.getElementById("titulo-dialog-cliente").textContent = "Editar cliente";
  dialogCliente.showModal();
}

async function removerCliente(id) {
  if (!confirm("Excluir este cliente?")) return;
  await Api.excluirCliente(id);
  carregarClientes();
}

formCliente.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const id = document.getElementById("cliente-id").value;
  const dados = {
    nome: document.getElementById("cliente-nome").value,
    cpf_cnpj: document.getElementById("cliente-cpf-cnpj").value,
    telefone: document.getElementById("cliente-telefone").value,
    email: document.getElementById("cliente-email").value,
    endereco: document.getElementById("cliente-endereco").value,
    limite_fiado: document.getElementById("cliente-limite-fiado").value || 0,
  };

  if (id) {
    await Api.atualizarCliente(id, dados);
  } else {
    await Api.criarCliente(dados);
  }

  dialogCliente.close();
  formCliente.reset();
  carregarClientes();
});

document.getElementById("btn-novo-cliente").addEventListener("click", abrirDialogCliente);
document.getElementById("btn-cancelar-cliente").addEventListener("click", () => dialogCliente.close());
document.getElementById("busca-cliente").addEventListener("input", carregarClientes);

document.addEventListener("DOMContentLoaded", carregarClientes);
