from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.auth import autenticar_usuario, criar_token, verificar_senha
from app.database import get_db

router = APIRouter()

@router.post("/login/")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = autenticar_usuario(db, form_data.username, form_data.password)

    if not usuario:
        raise HTTPException(status_code=401, detail="Credenciais inválidas.")

    # ✅ Criar token JWT com o ID do usuário
    access_token = criar_token({"sub": str(usuario.id)})

    # ✅ Verificar se o usuário ainda está com a senha padrão
    usando_senha_padrao = verificar_senha("123456", usuario.senha)

    return {
        "access_token": access_token,
        "id": usuario.id,
        "perfil": usuario.role.nome,
        "nome": usuario.nome,
        "cpf": usuario.cpf,
        "foto_url": "",  # ✅ Campo vazio temporário até você criar na tabela futuramente
        "senha_padrao": verificar_senha("123456", usuario.senha)  # ✅ Muito importante!
    }
