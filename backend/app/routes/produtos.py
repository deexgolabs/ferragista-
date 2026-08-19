import csv
import io

from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models.produto import Produto, UNIDADES_VALIDAS
from app.models.categoria import Categoria
from app.models.loja import Loja
from app.utils.rbac import perfis_permitidos
from app.utils.tenant import query_tenant, loja_atual_id
from app.utils.barcode_gen import gerar_codigo_barras_png

produtos_bp = Blueprint("produtos", __name__)
_GESTAO = ("admin", "gerente", "estoquista")


@produtos_bp.get("")
@jwt_required()
def listar_produtos():
    query = query_tenant(Produto)

    busca = request.args.get("busca")
    if busca:
        query = query.filter(
            db.or_(Produto.nome.ilike(f"%{busca}%"), Produto.codigo.ilike(f"%{busca}%"))
        )
    if request.args.get("categoria_id"):
        query = query.filter_by(categoria_id=request.args.get("categoria_id", type=int))
    if request.args.get("estoque_baixo") == "true":
        query = query.filter(Produto.quantidade_estoque <= Produto.estoque_minimo)
    if request.args.get("ativo") is not None:
        query = query.filter_by(ativo=request.args.get("ativo") == "true")

    produtos = query.order_by(Produto.nome).all()
    return jsonify([p.to_dict() for p in produtos])


@produtos_bp.get("/<int:produto_id>")
@jwt_required()
def obter_produto(produto_id):
    produto = query_tenant(Produto).filter_by(id=produto_id).first_or_404()
    return jsonify(produto.to_dict())


@produtos_bp.post("")
@perfis_permitidos(*_GESTAO)
def criar_produto():
    dados = request.get_json() or {}
    if not dados.get("nome"):
        return jsonify({"erro": "nome é obrigatório"}), 400

    unidade = dados.get("unidade", "un")
    if unidade not in UNIDADES_VALIDAS:
        return jsonify({"erro": f"unidade inválida. Use uma de: {', '.join(UNIDADES_VALIDAS)}"}), 400

    loja_id = loja_atual_id()
    loja = db.session.get(Loja, loja_id)
    limite = loja.limite_produtos() if loja else None
    if limite is not None and Produto.query.filter_by(loja_id=loja_id).count() >= limite:
        return jsonify({"erro": f"limite de {limite} produtos do plano atual atingido"}), 402

    produto = Produto(
        loja_id=loja_id,
        nome=dados["nome"],
        codigo=dados.get("codigo"),
        categoria_id=dados.get("categoria_id"),
        unidade=unidade,
        preco_custo=dados.get("preco_custo"),
        preco_venda=dados.get("preco_venda", 0),
        quantidade_estoque=dados.get("quantidade_estoque", 0),
        estoque_minimo=dados.get("estoque_minimo", 0),
    )
    db.session.add(produto)
    db.session.commit()
    return jsonify(produto.to_dict()), 201


@produtos_bp.put("/<int:produto_id>")
@perfis_permitidos(*_GESTAO)
def atualizar_produto(produto_id):
    produto = query_tenant(Produto).filter_by(id=produto_id).first_or_404()
    dados = request.get_json() or {}

    if "unidade" in dados and dados["unidade"] not in UNIDADES_VALIDAS:
        return jsonify({"erro": f"unidade inválida. Use uma de: {', '.join(UNIDADES_VALIDAS)}"}), 400

    for campo in ["nome", "codigo", "categoria_id", "unidade", "preco_custo", "preco_venda", "estoque_minimo", "ativo"]:
        if campo in dados:
            setattr(produto, campo, dados[campo])

    db.session.commit()
    return jsonify(produto.to_dict())


@produtos_bp.delete("/<int:produto_id>")
@perfis_permitidos(*_GESTAO)
def excluir_produto(produto_id):
    produto = query_tenant(Produto).filter_by(id=produto_id).first_or_404()
    db.session.delete(produto)
    db.session.commit()
    return "", 204


@produtos_bp.get("/<int:produto_id>/codigo-barras.png")
@jwt_required()
def codigo_barras_produto(produto_id):
    produto = query_tenant(Produto).filter_by(id=produto_id).first_or_404()
    if not produto.codigo:
        return jsonify({"erro": "este produto não tem código/SKU cadastrado"}), 400

    try:
        imagem = gerar_codigo_barras_png(produto.codigo)
    except Exception:
        return jsonify({"erro": "não foi possível gerar o código de barras para este código"}), 400

    return send_file(io.BytesIO(imagem), mimetype="image/png")


@produtos_bp.post("/importar-csv")
@perfis_permitidos(*_GESTAO)
def importar_produtos_csv():
    """Importa produtos em lote de um CSV com cabeçalho:
    nome,codigo,categoria,unidade,preco_custo,preco_venda,quantidade_estoque,estoque_minimo
    Apenas `nome` é obrigatório. Categorias novas são criadas automaticamente
    pelo nome. Linhas com erro são reportadas, mas não interrompem a importação
    das demais."""
    arquivo = request.files.get("arquivo")
    if not arquivo:
        return jsonify({"erro": "arquivo é obrigatório"}), 400

    loja_id = loja_atual_id()
    try:
        conteudo = arquivo.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        return jsonify({"erro": "não foi possível ler o arquivo — salve o CSV em UTF-8"}), 400

    leitor = csv.DictReader(io.StringIO(conteudo))
    if not leitor.fieldnames or "nome" not in [c.strip().lower() for c in leitor.fieldnames]:
        return jsonify({"erro": "CSV inválido — a coluna 'nome' é obrigatória no cabeçalho"}), 400

    categorias_existentes = {c.nome.lower(): c for c in Categoria.query.filter_by(loja_id=loja_id).all()}

    criados = 0
    erros = []
    for numero_linha, linha in enumerate(leitor, start=2):
        linha = {(chave or "").strip().lower(): (valor or "").strip() for chave, valor in linha.items()}
        nome = linha.get("nome")
        if not nome:
            erros.append(f"linha {numero_linha}: nome vazio, ignorada")
            continue

        unidade = linha.get("unidade") or "un"
        if unidade not in UNIDADES_VALIDAS:
            erros.append(f"linha {numero_linha}: unidade '{unidade}' inválida, usando 'un'")
            unidade = "un"

        categoria_id = None
        nome_categoria = linha.get("categoria")
        if nome_categoria:
            categoria = categorias_existentes.get(nome_categoria.lower())
            if not categoria:
                categoria = Categoria(loja_id=loja_id, nome=nome_categoria)
                db.session.add(categoria)
                db.session.flush()
                categorias_existentes[nome_categoria.lower()] = categoria
            categoria_id = categoria.id

        def _numero(chave, padrao=0):
            valor = linha.get(chave)
            try:
                return float(valor.replace(",", ".")) if valor else padrao
            except ValueError:
                erros.append(f"linha {numero_linha}: valor inválido em '{chave}', usando {padrao}")
                return padrao

        produto = Produto(
            loja_id=loja_id,
            nome=nome,
            codigo=linha.get("codigo") or None,
            categoria_id=categoria_id,
            unidade=unidade,
            preco_custo=_numero("preco_custo", None),
            preco_venda=_numero("preco_venda", 0),
            quantidade_estoque=_numero("quantidade_estoque", 0),
            estoque_minimo=_numero("estoque_minimo", 0),
        )
        db.session.add(produto)
        criados += 1

    db.session.commit()
    return jsonify({"criados": criados, "erros": erros})


# ===== Categorias =====

@produtos_bp.get("/categorias")
@jwt_required()
def listar_categorias():
    categorias = query_tenant(Categoria).order_by(Categoria.nome).all()
    return jsonify([c.to_dict() for c in categorias])


@produtos_bp.post("/categorias")
@perfis_permitidos(*_GESTAO)
def criar_categoria():
    dados = request.get_json() or {}
    if not dados.get("nome"):
        return jsonify({"erro": "nome é obrigatório"}), 400

    categoria = Categoria(loja_id=loja_atual_id(), nome=dados["nome"])
    db.session.add(categoria)
    db.session.commit()
    return jsonify(categoria.to_dict()), 201


@produtos_bp.delete("/categorias/<int:categoria_id>")
@perfis_permitidos(*_GESTAO)
def excluir_categoria(categoria_id):
    categoria = query_tenant(Categoria).filter_by(id=categoria_id).first_or_404()
    db.session.delete(categoria)
    db.session.commit()
    return "", 204
