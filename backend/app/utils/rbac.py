from functools import wraps

from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt


def perfis_permitidos(*perfis):
    """Libera acesso se o perfil do usuário autenticado estiver em `perfis`."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("perfil") in perfis:
                return fn(*args, **kwargs)
            return jsonify({"erro": "acesso negado para o seu perfil"}), 403

        return wrapper

    return decorator
