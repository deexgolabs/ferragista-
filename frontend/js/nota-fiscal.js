async function carregarConfigNfe() {
  const config = await Api.obterConfigNfe();
  document.getElementById("nfe-provedor").value = config.nfe_provedor || "";
  document.getElementById("nfe-ambiente").value = config.nfe_ambiente;
  document.getElementById("nfe-cnpj").value = config.nfe_cnpj_emitente || "";
  document.getElementById("nfe-chave-atual").textContent = config.nfe_api_key_configurada
    ? `Chave atual: ${config.nfe_api_key_mascarada}`
    : "Nenhuma chave configurada ainda.";
}

document.getElementById("form-config-nfe").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const mensagemEl = document.getElementById("mensagem-config-nfe");
  try {
    await Api.atualizarConfigNfe({
      nfe_provedor: document.getElementById("nfe-provedor").value,
      nfe_ambiente: document.getElementById("nfe-ambiente").value,
      nfe_cnpj_emitente: document.getElementById("nfe-cnpj").value,
      nfe_api_key: document.getElementById("nfe-api-key").value,
    });
    document.getElementById("nfe-api-key").value = "";
    mensagemEl.textContent = "Configuração salva.";
    mensagemEl.style.color = "var(--cor-sucesso)";
    mensagemEl.classList.remove("oculto");
    await carregarConfigNfe();
  } catch (erro) {
    mensagemEl.textContent = erro.message;
    mensagemEl.style.color = "var(--cor-erro)";
    mensagemEl.classList.remove("oculto");
  }
});

document.addEventListener("DOMContentLoaded", carregarConfigNfe);
