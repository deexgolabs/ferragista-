const dialogUsuario = document.getElementById("dialog-usuario");
const formUsuario = document.getElementById("form-usuario");
let usuariosCache = [];

async function carregarUsuarios() {
  usuariosCache = await Api.listarUsuarios();
  document.getElementById("tabela-usuarios").innerHTML =
    usuariosCache
      .map(
        (u) => `
          <tr>
            <td>${u.nome}</td>
            <td>${u.email}</td>
            <td style="text-transform: capitalize;">${u.perfil}</td>
            <td><span class="selo ${u.ativo ? "selo-ativo" : "selo-inativo"}">${u.ativo ? "ativo" : "inativo"}</span></td>
            <td>
              <button class="btn btn-secundario" onclick="editarUsuario(${u.id})">Editar</button>
              <button class="btn btn-perigo" onclick="removerUsuario(${u.id})">Excluir</button>
            </td>
          </tr>
        `
      )
      .join("") || "<tr><td colspan='5'>Nenhum usuário cadastrado.</td></tr>";
}

function abrirDialogUsuario() {
  formUsuario.reset();
  document.getElementById("usuario-id").value = "";
  document.getElementById("titulo-dialog-usuario").textContent = "Novo usuário";
  document.getElementById("campo-usuario-email").classList.remove("oculto");
  document.getElementById("campo-usuario-senha").classList.remove("oculto");
  document.getElementById("usuario-senha").required = true;
  document.getElementById("campo-usuario-ativo").classList.add("oculto");
  dialogUsuario.showModal();
}

function editarUsuario(id) {
  const usuario = usuariosCache.find((u) => u.id === id);
  if (!usuario) return;

  document.getElementById("usuario-id").value = usuario.id;
  document.getElementById("usuario-nome").value = usuario.nome;
  document.getElementById("usuario-perfil").value = usuario.perfil;
  document.getElementById("usuario-comissao").value = usuario.percentual_comissao;
  document.getElementById("usuario-ativo").checked = usuario.ativo;
  document.getElementById("titulo-dialog-usuario").textContent = "Editar usuário";
  document.getElementById("campo-usuario-email").classList.add("oculto");
  document.getElementById("campo-usuario-senha").classList.add("oculto");
  document.getElementById("usuario-senha").required = false;
  document.getElementById("campo-usuario-ativo").classList.remove("oculto");
  dialogUsuario.showModal();
}

async function removerUsuario(id) {
  if (!confirm("Excluir este usuário?")) return;
  try {
    await Api.excluirUsuario(id);
    carregarUsuarios();
  } catch (erro) {
    alert(erro.message);
  }
}

formUsuario.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const id = document.getElementById("usuario-id").value;

  try {
    if (id) {
      await Api.atualizarUsuario(id, {
        nome: document.getElementById("usuario-nome").value,
        perfil: document.getElementById("usuario-perfil").value,
        ativo: document.getElementById("usuario-ativo").checked,
        percentual_comissao: document.getElementById("usuario-comissao").value || 0,
      });
    } else {
      await Api.criarUsuario({
        nome: document.getElementById("usuario-nome").value,
        email: document.getElementById("usuario-email").value,
        senha: document.getElementById("usuario-senha").value,
        perfil: document.getElementById("usuario-perfil").value,
      });
    }
    dialogUsuario.close();
    formUsuario.reset();
    carregarUsuarios();
  } catch (erro) {
    alert(erro.message);
  }
});

document.getElementById("btn-novo-usuario").addEventListener("click", abrirDialogUsuario);
document.getElementById("btn-cancelar-usuario").addEventListener("click", () => dialogUsuario.close());

document.addEventListener("DOMContentLoaded", carregarUsuarios);
