const dialogFornecedor = document.getElementById("dialog-fornecedor");
const formFornecedor = document.getElementById("form-fornecedor");
let fornecedoresCache = [];

async function carregarFornecedores() {
  const busca = document.getElementById("busca-fornecedor").value.trim();
  fornecedoresCache = await Api.listarFornecedores(busca ? `?busca=${encodeURIComponent(busca)}` : "");

  document.getElementById("tabela-fornecedores").innerHTML =
    fornecedoresCache
      .map(
        (f) => `
          <tr>
            <td>${f.nome}</td>
            <td>${f.cnpj || "—"}</td>
            <td>${f.telefone || "—"}</td>
            <td>${f.contato || "—"}</td>
            <td>
              <button class="btn btn-secundario" onclick="editarFornecedor(${f.id})">Editar</button>
              <button class="btn btn-perigo" onclick="removerFornecedor(${f.id})">Excluir</button>
            </td>
          </tr>
        `
      )
      .join("") || "<tr><td colspan='5'>Nenhum fornecedor cadastrado.</td></tr>";
}

function abrirDialogFornecedor() {
  formFornecedor.reset();
  document.getElementById("fornecedor-id").value = "";
  document.getElementById("titulo-dialog-fornecedor").textContent = "Novo fornecedor";
  dialogFornecedor.showModal();
}

function editarFornecedor(id) {
  const fornecedor = fornecedoresCache.find((f) => f.id === id);
  if (!fornecedor) return;

  document.getElementById("fornecedor-id").value = fornecedor.id;
  document.getElementById("fornecedor-nome").value = fornecedor.nome;
  document.getElementById("fornecedor-cnpj").value = fornecedor.cnpj || "";
  document.getElementById("fornecedor-telefone").value = fornecedor.telefone || "";
  document.getElementById("fornecedor-email").value = fornecedor.email || "";
  document.getElementById("fornecedor-contato").value = fornecedor.contato || "";
  document.getElementById("fornecedor-endereco").value = fornecedor.endereco || "";
  document.getElementById("titulo-dialog-fornecedor").textContent = "Editar fornecedor";
  dialogFornecedor.showModal();
}

async function removerFornecedor(id) {
  if (!confirm("Excluir este fornecedor?")) return;
  await Api.excluirFornecedor(id);
  carregarFornecedores();
}

formFornecedor.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const id = document.getElementById("fornecedor-id").value;
  const dados = {
    nome: document.getElementById("fornecedor-nome").value,
    cnpj: document.getElementById("fornecedor-cnpj").value,
    telefone: document.getElementById("fornecedor-telefone").value,
    email: document.getElementById("fornecedor-email").value,
    contato: document.getElementById("fornecedor-contato").value,
    endereco: document.getElementById("fornecedor-endereco").value,
  };

  if (id) {
    await Api.atualizarFornecedor(id, dados);
  } else {
    await Api.criarFornecedor(dados);
  }

  dialogFornecedor.close();
  formFornecedor.reset();
  carregarFornecedores();
});

document.getElementById("btn-novo-fornecedor").addEventListener("click", abrirDialogFornecedor);
document.getElementById("btn-cancelar-fornecedor").addEventListener("click", () => dialogFornecedor.close());
document.getElementById("busca-fornecedor").addEventListener("input", carregarFornecedores);

document.addEventListener("DOMContentLoaded", carregarFornecedores);
