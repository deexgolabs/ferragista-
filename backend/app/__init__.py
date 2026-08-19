from flask import Flask

from app.config import Config
from app.extensions import db, migrate, jwt, cors, mail, limiter


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)

    register_blueprints(app)

    return app


def register_blueprints(app):
    from app.routes.auth import auth_bp
    from app.routes.publico import publico_bp
    from app.routes.central import central_bp
    from app.routes.produtos import produtos_bp
    from app.routes.estoque import estoque_bp
    from app.routes.fornecedores import fornecedores_bp
    from app.routes.compras import compras_bp
    from app.routes.clientes import clientes_bp
    from app.routes.vendas import vendas_bp
    from app.routes.financeiro import financeiro_bp
    from app.routes.relatorios import relatorios_bp
    from app.routes.caixa import caixa_bp
    from app.routes.loja_config import loja_config_bp
    from app.routes.sistema import sistema_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(publico_bp, url_prefix="/api/publico")
    app.register_blueprint(central_bp, url_prefix="/api/central")
    app.register_blueprint(produtos_bp, url_prefix="/api/produtos")
    app.register_blueprint(estoque_bp, url_prefix="/api/estoque")
    app.register_blueprint(fornecedores_bp, url_prefix="/api/fornecedores")
    app.register_blueprint(compras_bp, url_prefix="/api/compras")
    app.register_blueprint(clientes_bp, url_prefix="/api/clientes")
    app.register_blueprint(vendas_bp, url_prefix="/api/vendas")
    app.register_blueprint(financeiro_bp, url_prefix="/api/financeiro")
    app.register_blueprint(relatorios_bp, url_prefix="/api/relatorios")
    app.register_blueprint(caixa_bp, url_prefix="/api/caixa")
    app.register_blueprint(loja_config_bp, url_prefix="/api/loja")
    app.register_blueprint(sistema_bp, url_prefix="/api")
