from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from passlib.context import CryptContext

from app.models import User
from app.database import get_db

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class DefinirSenhaRequest(BaseModel):
    senha: str

@router.post("/usuarios/definir-senha/{token}")
def definir_senha(token: str, dados: DefinirSenhaRequest, db: Session = Depends(get_db)):
    if not token.startswith("convite-"):
        raise HTTPException(status_code=400, detail="Token inválido")

    try:
        usuario_id = int(token.replace("convite-", ""))
    except ValueError:
        raise HTTPException(status_code=400, detail="Token malformado")

    usuario = db.query(User).filter(User.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    senha_criptografada = pwd_context.hash(dados.senha)
    usuario.senha = senha_criptografada
    usuario.ativo = True
    db.commit()

    return {"mensagem": "Senha definida com sucesso"}
