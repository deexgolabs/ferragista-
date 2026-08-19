function exigirAutenticacao() {
  if (!getToken()) {
    window.location.href = "/pages/login.html";
  }
}

function sair() {
  limparSessao();
  window.location.href = "/pages/login.html";
}

document.addEventListener("DOMContentLoaded", () => {
  const formLogin = document.getElementById("form-login");
  if (!formLogin) return;

  formLogin.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const email = document.getElementById("email").value;
    const senha = document.getElementById("senha").value;
    const erroEl = document.getElementById("erro-login");

    try {
      const resultado = await Api.login(email, senha);
      setToken(resultado.access_token);
      localStorage.setItem("usuario", JSON.stringify(resultado.usuario));
      let destino = "/pages/dashboard.html";
      if (resultado.usuario.perfil === "super_admin") destino = "/pages/central-dashboard.html";
      window.location.href = destino;
    } catch (erro) {
      erroEl.textContent = erro.message;
      erroEl.classList.remove("oculto");
    }
  });
});
