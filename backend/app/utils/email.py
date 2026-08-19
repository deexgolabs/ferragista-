from flask import current_app
from flask_mail import Message

from app.extensions import mail


def enviar_email(destinatario: str, assunto: str, corpo: str) -> None:
    """Envia um e-mail se MAIL_SERVER estiver configurado; senão, apenas
    imprime no console — suficiente para testar o fluxo em desenvolvimento."""
    if not current_app.config.get("MAIL_SERVER"):
        print(f"[e-mail simulado] Para: {destinatario} | Assunto: {assunto}\n{corpo}\n")
        return

    mensagem = Message(subject=assunto, recipients=[destinatario], body=corpo)
    mail.send(mensagem)
