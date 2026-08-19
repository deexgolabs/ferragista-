const API_BASE_URL = "http://localhost:5000/api";

function getToken() {
  return localStorage.getItem("token");
}

function setToken(token) {
  localStorage.setItem("token", token);
}

function limparSessao() {
  localStorage.removeItem("token");
  localStorage.removeItem("usuario");
}

async function apiRequest(caminho, { method = "GET", body = null } = {}) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const resposta = await fetch(`${API_BASE_URL}${caminho}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : null,
  });

  if (resposta.status === 401 && token) {
    limparSessao();
    window.location.href = "/pages/login.html";
    return null;
  }

  if (resposta.status === 204) {
    return null;
  }

  const dados = await resposta.json().catch(() => null);

  if (!resposta.ok) {
    throw new Error((dados && dados.erro) || "Erro ao comunicar com o servidor");
  }

  return dados;
}

async function apiImagemUrl(caminho) {
  const headers = {};
  const token = getToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const resposta = await fetch(`${API_BASE_URL}${caminho}`, { headers });
  if (!resposta.ok) {
    const dados = await resposta.json().catch(() => null);
    throw new Error((dados && dados.erro) || "Erro ao gerar imagem");
  }
  const blob = await resposta.blob();
  return URL.createObjectURL(blob);
}

async function apiUpload(caminho, formData) {
  const headers = {};
  const token = getToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const resposta = await fetch(`${API_BASE_URL}${caminho}`, {
    method: "POST",
    headers,
    body: formData,
  });

  if (resposta.status === 401) {
    limparSessao();
    window.location.href = "/pages/login.html";
    return null;
  }

  const dados = await resposta.json().catch(() => null);
  if (!resposta.ok) {
    throw new Error((dados && dados.erro) || "Erro ao enviar arquivo");
  }
  return dados;
}

const Api = {
  login: (email, senha) => apiRequest("/auth/login", { method: "POST", body: { email, senha } }),
  cadastrarLoja: (dados) => apiRequest("/publico/cadastrar-loja", { method: "POST", body: dados }),

  listarLojasCentral: () => apiRequest("/central/lojas"),
  atualizarLojaCentral: (id, dados) => apiRequest(`/central/lojas/${id}`, { method: "PUT", body: dados }),
  metricasCentral: () => apiRequest("/central/metricas"),
  crescimentoCentral: () => apiRequest("/central/crescimento"),
  analyticsCentral: () => apiRequest("/central/analytics"),

  me: () => apiRequest("/auth/me"),
  atualizarMeuPerfil: (dados) => apiRequest("/auth/me", { method: "PUT", body: dados }),
  esqueciSenha: (email) => apiRequest("/auth/esqueci-senha", { method: "POST", body: { email } }),
  redefinirSenha: (token, novaSenha) =>
    apiRequest("/auth/redefinir-senha", { method: "POST", body: { token, nova_senha: novaSenha } }),
  trocarSenha: (senhaAtual, novaSenha) =>
    apiRequest("/auth/trocar-senha", { method: "POST", body: { senha_atual: senhaAtual, nova_senha: novaSenha } }),

  listarUsuarios: () => apiRequest("/auth/usuarios"),
  criarUsuario: (dados) => apiRequest("/auth/registrar", { method: "POST", body: dados }),
  atualizarUsuario: (id, dados) => apiRequest(`/auth/usuarios/${id}`, { method: "PUT", body: dados }),
  excluirUsuario: (id) => apiRequest(`/auth/usuarios/${id}`, { method: "DELETE" }),

  listarProdutos: (params = "") => apiRequest(`/produtos${params}`),
  obterProduto: (id) => apiRequest(`/produtos/${id}`),
  criarProduto: (dados) => apiRequest("/produtos", { method: "POST", body: dados }),
  atualizarProduto: (id, dados) => apiRequest(`/produtos/${id}`, { method: "PUT", body: dados }),
  excluirProduto: (id) => apiRequest(`/produtos/${id}`, { method: "DELETE" }),
  importarProdutosCsv: (arquivo) => {
    const formData = new FormData();
    formData.append("arquivo", arquivo);
    return apiUpload("/produtos/importar-csv", formData);
  },
  urlCodigoBarrasProduto: (id) => apiImagemUrl(`/produtos/${id}/codigo-barras.png`),

  listarCategorias: () => apiRequest("/produtos/categorias"),
  criarCategoria: (dados) => apiRequest("/produtos/categorias", { method: "POST", body: dados }),
  excluirCategoria: (id) => apiRequest(`/produtos/categorias/${id}`, { method: "DELETE" }),

  listarMovimentacoes: (params = "") => apiRequest(`/estoque/movimentacoes${params}`),
  criarMovimentacao: (dados) => apiRequest("/estoque/movimentacoes", { method: "POST", body: dados }),

  listarFornecedores: (params = "") => apiRequest(`/fornecedores${params}`),
  criarFornecedor: (dados) => apiRequest("/fornecedores", { method: "POST", body: dados }),
  atualizarFornecedor: (id, dados) => apiRequest(`/fornecedores/${id}`, { method: "PUT", body: dados }),
  excluirFornecedor: (id) => apiRequest(`/fornecedores/${id}`, { method: "DELETE" }),

  listarCompras: (params = "") => apiRequest(`/compras${params}`),
  obterCompra: (id) => apiRequest(`/compras/${id}`),
  criarCompra: (dados) => apiRequest("/compras", { method: "POST", body: dados }),
  receberCompra: (id, dados = {}) => apiRequest(`/compras/${id}/receber`, { method: "PUT", body: dados }),
  cancelarCompra: (id) => apiRequest(`/compras/${id}/cancelar`, { method: "PUT" }),
  excluirCompra: (id) => apiRequest(`/compras/${id}`, { method: "DELETE" }),

  listarClientes: (params = "") => apiRequest(`/clientes${params}`),
  criarCliente: (dados) => apiRequest("/clientes", { method: "POST", body: dados }),
  atualizarCliente: (id, dados) => apiRequest(`/clientes/${id}`, { method: "PUT", body: dados }),
  excluirCliente: (id) => apiRequest(`/clientes/${id}`, { method: "DELETE" }),

  listarVendas: (params = "") => apiRequest(`/vendas${params}`),
  obterVenda: (id) => apiRequest(`/vendas/${id}`),
  criarVenda: (dados) => apiRequest("/vendas", { method: "POST", body: dados }),
  cancelarVenda: (id) => apiRequest(`/vendas/${id}/cancelar`, { method: "PUT" }),

  listarLancamentos: (params = "") => apiRequest(`/financeiro${params}`),
  resumoFinanceiro: () => apiRequest("/financeiro/resumo"),
  criarLancamento: (dados) => apiRequest("/financeiro", { method: "POST", body: dados }),
  atualizarLancamento: (id, dados) => apiRequest(`/financeiro/${id}`, { method: "PUT", body: dados }),
  quitarLancamento: (id) => apiRequest(`/financeiro/${id}/quitar`, { method: "PUT" }),
  excluirLancamento: (id) => apiRequest(`/financeiro/${id}`, { method: "DELETE" }),

  dashboard: () => apiRequest("/relatorios/dashboard"),
  produtosMaisVendidos: (dias) => apiRequest(`/relatorios/produtos-mais-vendidos?dias=${dias || 30}`),
  vendasPorPeriodo: (dias) => apiRequest(`/relatorios/vendas-por-periodo?dias=${dias || 30}`),
  estoqueBaixo: () => apiRequest("/relatorios/estoque-baixo"),
  notificacoes: () => apiRequest("/relatorios/notificacoes"),
  curvaAbc: (dias) => apiRequest(`/relatorios/curva-abc?dias=${dias || 30}`),
  margem: (dias) => apiRequest(`/relatorios/margem?dias=${dias || 30}`),
  comissoes: (dias) => apiRequest(`/relatorios/comissoes?dias=${dias || 30}`),

  caixaAtual: () => apiRequest("/caixa/atual"),
  listarSessoesCaixa: () => apiRequest("/caixa/sessoes"),
  abrirCaixa: (valorAbertura) => apiRequest("/caixa/abrir", { method: "POST", body: { valor_abertura: valorAbertura } }),
  fecharCaixa: (dados) => apiRequest("/caixa/fechar", { method: "PUT", body: dados }),
  listarMovimentacoesCaixa: () => apiRequest("/caixa/movimentacoes"),
  criarMovimentacaoCaixa: (dados) => apiRequest("/caixa/movimentacoes", { method: "POST", body: dados }),

  obterConfigNfe: () => apiRequest("/loja/config-nfe"),
  atualizarConfigNfe: (dados) => apiRequest("/loja/config-nfe", { method: "PUT", body: dados }),

  health: () => apiRequest("/health"),
};
