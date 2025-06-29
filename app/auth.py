from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, Query, Request
from sqlalchemy.orm import Session, joinedload
from . import models, database
from dotenv import load_dotenv
from app.models import User
import os
from typing import Optional

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def criptografar_senha(senha: str) -> str:
    return pwd_context.hash(senha)

def verificar_senha(senha: str, hash: str):
    return pwd_context.verify(senha, hash)

def criar_token(dados: dict) -> str:
    to_encode = dados.copy()
    expira = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expira})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def autenticar_usuario(db, username: str, password: str):
    usuario = db.query(User).filter(User.email == username).first()
    if not usuario:
        return False
    if not verificar_senha(password, usuario.senha):
        return False
    if not usuario.ativo and not verificar_senha("123456", usuario.senha):
        raise HTTPException(status_code=403, detail="Usuário desativado. Entre em contato com o administrador.")
    return usuario

# =============================
# VERSÃO 1 - STRICT: Apenas Header Authorization
# =============================

def get_current_user_strict(
    request: Request,
    db: database.Session = Depends(database.get_db)
) -> models.User:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token de autenticação ausente no Header.")

    token = auth_header.split(" ")[1]
    return validar_token_e_carregar_usuario(token, db)

# =============================
# VERSÃO 2 - FLEX: Header OU Query String (Usada só no HTML)
# =============================

def get_current_user_flex(
    request: Request,
    token_query: Optional[str] = Query(default=None, alias="token"),
    db: database.Session = Depends(database.get_db)
) -> models.User:
    auth_header = request.headers.get("Authorization")
    header_token = None

    if auth_header and auth_header.startswith("Bearer "):
        header_token = auth_header.split(" ")[1]

    # ✅ Prioridade: Query String primeiro, depois Header
    token = token_query if token_query else header_token

    print(f"DEBUG - Token da query: {token_query}")
    print(f"DEBUG - Token do header: {header_token}")

    if not token:
        raise HTTPException(status_code=401, detail="Token ausente na query ou no header.")

    return validar_token_e_carregar_usuario(token, db)

# =============================
# Validação centralizada do token
# =============================

def validar_token_e_carregar_usuario(token: str, db: database.Session) -> models.User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        print(f"DEBUG - ID extraído do token: {user_id}")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token inválido: sub ausente")
    except JWTError as e:
        print(f"DEBUG - Erro ao decodificar token: {e}")
        raise HTTPException(status_code=401, detail="Token inválido")

    try:
        user_id_int = int(user_id)
    except ValueError:
        print(f"DEBUG - sub inválido no token: {user_id}")
        raise HTTPException(status_code=401, detail="Token inválido - sub numérico")

    user = (
        db.query(models.User)
        .options(joinedload(models.User.role))
        .filter(models.User.id == user_id_int)
        .first()
    )

    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")

    print(f"DEBUG - Usuário carregado: ID={user.id}, Perfil={user.role.nome}")

    return user
