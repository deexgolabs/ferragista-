from app.extensions import db


class Categoria(db.Model):
    __tablename__ = "categorias"

    id = db.Column(db.Integer, primary_key=True)
    loja_id = db.Column(db.Integer, db.ForeignKey("lojas.id"), nullable=False)
    nome = db.Column(db.String(80), nullable=False)

    def to_dict(self) -> dict:
        return {"id": self.id, "nome": self.nome}
