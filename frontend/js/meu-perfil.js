async function carregarPerfil() {
  const usuario = await Api.me();
  document.getElementById("perfil-nome").value = usuario.nome;
  document.getElementById("perfil-email").value = usuario.email;
}

document.getElementById("form-perfil").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const mensagemEl = document.getElementById("mensagem-perfil");
  try {
    const usuario = await Api.atualizarMeuPerfil({
      nome: document.getElementById("perfil-nome").value,
      email: document.getElementById("perfil-email").value,
    });
    localStorage.setItem("usuario", JSON.stringify(usuario));
    mensagemEl.textContent = "Dados atualizados com sucesso.";
    mensagemEl.style.color = "var(--cor-sucesso)";
    mensagemEl.classList.remove("oculto");
  } catch (erro) {
    mensagemEl.textContent = erro.message;
    mensagemEl.style.color = "var(--cor-erro)";
    mensagemEl.classList.remove("oculto");
  }
});

document.getElementById("form-senha").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const mensagemEl = document.getElementById("mensagem-senha");
  try {
    await Api.trocarSenha(document.getElementById("senha-atual").value, document.getElementById("senha-nova").value);
    mensagemEl.textContent = "Senha alterada com sucesso.";
    mensagemEl.style.color = "var(--cor-sucesso)";
    mensagemEl.classList.remove("oculto");
    evento.target.reset();
  } catch (erro) {
    mensagemEl.textContent = erro.message;
    mensagemEl.style.color = "var(--cor-erro)";
    mensagemEl.classList.remove("oculto");
  }
});

document.addEventListener("DOMContentLoaded", carregarPerfil);
