from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta
import secrets
from passlib.context import CryptContext
from pydantic import BaseModel

from app import models, schemas, auth
from app.database import get_db
from app.auth import get_current_user_strict, criptografar_senha, verificar_senha
from utils.validators import validar_forca_senha
from app.models import User, ConviteUsuario
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import joinedload
from app.schemas import UserCreate
from app.auth import get_current_user_strict

router = APIRouter(prefix="/usuarios", tags=["Usuários"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AlterarSenhaRequest(BaseModel):
    nova_senha: str

@router.get("/", response_model=list[schemas.UserOut])
def listar_usuarios(db: Session = Depends(get_db)):
    usuarios = (
        db.query(User)
        .options(joinedload(User.role))
        .filter(User.role_id.isnot(None))  # ✅ Filtra apenas quem tem role_id preenchido
        .all()
    )

    usuarios_out = []

    for usuario in usuarios:
        usuarios_out.append({
            "id": usuario.id,
            "nome": usuario.nome,
            "cpf": usuario.cpf,
            "email": usuario.email,
            "ativo": usuario.ativo,
            "perfil": usuario.role.nome if usuario.role else "Sem Perfil",
            "cep": usuario.cep,
            "rua": usuario.rua,
            "numero": usuario.numero,
            "complemento": usuario.complemento,
            "bairro": usuario.bairro,
            "cidade": usuario.cidade,
            "estado": usuario.estado,
            "telefone": usuario.telefone
        })

    return usuarios_out

@router.post("/{usuario_id}/alterar-senha")
def alterar_senha(usuario_id: int, dados: AlterarSenhaRequest, db: Session = Depends(get_db)):
    erros = validar_forca_senha(dados.nova_senha)
    if erros:
        raise HTTPException(status_code=400, detail=erros)

    usuario = db.query(User).filter(User.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    hash_nova = pwd_context.hash(dados.nova_senha)
    usuario.senha = hash_nova

    # ✅ Reativa o usuário após alterar a senha
    usuario.ativo = True

    db.commit()
    return {"mensagem": "Senha alterada com sucesso."}

@router.get("/me", response_model=schemas.UserOut)
def get_me(usuario_logado=Depends(get_current_user_strict)):
    return usuario_logado

@router.get("/{usuario_id}", response_model=schemas.UserOut)
def obter_usuario_por_id(usuario_id: int, db: Session = Depends(get_db)):
    usuario = db.query(models.User).options(joinedload(models.User.role)).filter(models.User.id == usuario_id).first()
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return schemas.UserOut(
    id=usuario.id,
    nome=usuario.nome,
    email=usuario.email,
    cpf=usuario.cpf,
    perfil=usuario.role.nome if usuario.role else "Sem Perfil",
    ativo=usuario.ativo,  # ✅ ESSA LINHA FALTAVA
    cep=usuario.cep,
    rua=usuario.rua,
    numero=usuario.numero,
    complemento=usuario.complemento,
    bairro=usuario.bairro,
    cidade=usuario.cidade,
    estado=usuario.estado,
    telefone=usuario.telefone,
    data_nascimento=usuario.data_nascimento
    )


@router.post("/convite", response_model=schemas.ConviteOut)
def convidar_usuario(usuario: schemas.UserConvite, db: Session = Depends(get_db)):
    usuario_existente = db.query(models.User).filter(models.User.email == usuario.email).first()
    if usuario_existente:
        if usuario_existente.role_id != usuario.role_id:
            usuario_existente.role_id = usuario.role_id
            db.commit()
        usuario_final = usuario_existente
    else:
        usuario_final = models.User(
            nome=usuario.nome,
            email=usuario.email,
            cpf=usuario.cpf,
            role_id=usuario.role_id or 3,
            ativo=False
        )
        db.add(usuario_final)
        db.commit()
        db.refresh(usuario_final)
    
    token = secrets.token_urlsafe(32)
    expira_em = datetime.utcnow() + timedelta(hours=24)
    convite = ConviteUsuario(usuario_id=usuario_final.id, token=token, expira_em=expira_em)
    db.add(convite)
    db.commit()
    return {"token": token, "expira_em": expira_em}

@router.post("/definir-senha/{token}")
def definir_senha(token: str, dados: schemas.DefinirSenha, db: Session = Depends(get_db)):
    erros = validar_forca_senha(dados.senha)
    if erros:
        raise HTTPException(status_code=400, detail=erros)

    convite = db.query(ConviteUsuario).filter(ConviteUsuario.token == token).first()
    if not convite:
        raise HTTPException(status_code=404, detail="Token inválido.")
    if convite.usado_em is not None:
        raise HTTPException(status_code=400, detail="Este link já foi utilizado.")
    if convite.expira_em < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Este link expirou. Solicite um novo convite.")

    usuario = db.query(models.User).filter(models.User.id == convite.usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    usuario.senha = criptografar_senha(dados.senha)
    usuario.ativo = True
    convite.usado_em = datetime.utcnow()
    db.commit()

    return {"mensagem": "Senha definida com sucesso. Você já pode fazer login."}

@router.patch("/{id}/status")
def toggle_status(id: int, db: Session = Depends(get_db)):
    usuario = db.query(User).filter(User.id == id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    usuario.ativo = not usuario.ativo
    db.commit()
    return {"status": "sucesso", "ativo": usuario.ativo}

from fastapi import HTTPException, status

@router.put("/{usuario_id}")
def atualizar_usuario(usuario_id: int, dados: schemas.UserUpdate, db: Session = Depends(get_db), usuario_logado=Depends(get_current_user_strict)):
    usuario = db.query(User).filter(User.id == usuario_id).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    # ✅ Validação de permissão por perfil
    if usuario_logado.role.nome == "agente":
        # Agente só pode editar clientes
        if usuario.role.nome != "cliente":
            raise HTTPException(status_code=403, detail="Agente só pode editar usuários com perfil cliente.")

        # Agente só pode alterar nome, endereço, cep, número, telefone e perfil (limitado a cliente)
        if dados.email and dados.email != usuario.email:
            raise HTTPException(status_code=403, detail="Agente não pode alterar o e-mail.")

        if dados.cpf and dados.cpf != usuario.cpf:
            raise HTTPException(status_code=403, detail="Agente não pode alterar o CPF.")

        if dados.role_id and dados.role_id != 3:
            raise HTTPException(status_code=403, detail="Agente só pode definir perfil como cliente.")

    # ✅ Validação de unicidade (email e cpf)
    if dados.email and dados.email != usuario.email:
        email_existente = db.query(User).filter(User.email == dados.email, User.id != usuario_id).first()
        if email_existente:
            raise HTTPException(status_code=400, detail="Já existe outro usuário com este e-mail.")

    if dados.cpf and dados.cpf != usuario.cpf:
        cpf_existente = db.query(User).filter(User.cpf == dados.cpf, User.id != usuario_id).first()
        if cpf_existente:
            raise HTTPException(status_code=400, detail="Já existe outro usuário com este CPF.")

    # ✅ Atualização dos campos (só atualiza se o campo vier preenchido)
        if dados.nome: usuario.nome = dados.nome
        if dados.email and usuario_logado.role.nome == "admin": usuario.email = dados.email
        if dados.cpf and usuario_logado.role.nome == "admin": usuario.cpf = dados.cpf
        if dados.role_id: usuario.role_id = dados.role_id

        # Campos de endereço e telefone (ambos admin e agente podem alterar)
        if dados.cep: usuario.cep = dados.cep
        if dados.rua: usuario.rua = dados.rua
        if dados.numero: usuario.numero = dados.numero
        if dados.complemento: usuario.complemento = dados.complemento
        if dados.bairro: usuario.bairro = dados.bairro
        if dados.cidade: usuario.cidade = dados.cidade
        if dados.estado: usuario.estado = dados.estado
        if dados.telefone: usuario.telefone = dados.telefone
        if dados.data_nascimento is not None: usuario.data_nascimento = dados.data_nascimento

        db.commit()
        return {"mensagem": "Usuário atualizado com sucesso."}


@router.post("/{usuario_id}/reenviar-convite")
async def reenviar_convite(usuario_id: int, db: Session = Depends(get_db)):
    usuario = db.query(User).filter(User.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if not usuario.email:
        raise HTTPException(status_code=400, detail="Usuário sem e-mail cadastrado")

    token = f"convite-{usuario.id}"
    frontend_base_url = "http://localhost:8501"
    link_ativacao = f"{frontend_base_url}/?pagina=definir_senha&token={token}"

    try:
        await enviar_email_convite(usuario.nome, usuario.email, link_ativacao)
        return {"mensagem": "Convite reenviado com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao enviar e-mail: {e}")

@router.post("/{usuario_id}/redefinir-senha")
def redefinir_senha(usuario_id: int, db: Session = Depends(get_db)):
    usuario = db.query(User).filter(User.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    nova_senha = "123456"
    hash_senha = pwd_context.hash(nova_senha)
    usuario.senha = hash_senha

    # ✅ Desativa o usuário até ele trocar a senha
    usuario.ativo = False

    db.commit()

    return {"mensagem": f"Senha redefinida com sucesso para {nova_senha}"}

@router.delete("/{usuario_id}")
def excluir_usuario(usuario_id: int, db: Session = Depends(get_db), usuario_logado=Depends(get_current_user_strict)):
    usuario = db.query(User).filter(User.id == usuario_id).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    # ✅ Impedir exclusão do próprio usuário
    if usuario_logado.id == usuario.id:
        raise HTTPException(status_code=403, detail="Você não pode excluir o próprio usuário enquanto estiver logado.")

    # ✅ Apenas Admin pode excluir
    if usuario_logado.role.nome != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem excluir usuários.")

    try:
        # ✅ Excluir convites relacionados
        db.query(models.ConviteUsuario).filter(models.ConviteUsuario.usuario_id == usuario.id).delete()

        # ✅ Excluir o usuário
        db.delete(usuario)
        db.commit()
        return {"mensagem": "Usuário excluído com sucesso."}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao excluir usuário: {e}")

    
@router.post("/")
def criar_usuario(
    usuario: UserCreate,
    db: Session = Depends(get_db),
    usuario_logado: User = Depends(get_current_user_strict)
):
    # ✅ Validação de permissão por perfil logado
    perfil_logado = usuario_logado.role.nome.lower() if usuario_logado.role else "cliente"

    if perfil_logado == "agente" and usuario.role_id != 3:
        raise HTTPException(
            status_code=403,
            detail="Agentes só podem criar usuários com perfil Cliente."
        )

    # ✅ Verificar duplicidade de CPF (só bloqueia se já for usuário com role_id)
    cpf_existente = (
        db.query(User)
        .filter(User.cpf == usuario.cpf, User.role_id.isnot(None))
        .first()
    )
    if cpf_existente:
        raise HTTPException(status_code=400, detail="CPF já cadastrado como usuário do sistema.")

    # ✅ Verificar duplicidade de e-mail (só bloqueia se já for usuário com role_id)
    email_existente = (
        db.query(User)
        .filter(User.email == usuario.email, User.role_id.isnot(None))
        .first()
    )
    if email_existente:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado como usuário do sistema.")

    # ✅ Verificar se já existe um cliente com mesmo CPF e e-mail (sem role_id)
    cliente_existente = (
        db.query(User)
        .filter(User.cpf == usuario.cpf, User.email == usuario.email, User.role_id.is_(None))
        .first()
    )

    senha_inicial = "123456"
    hashed_password = pwd_context.hash(senha_inicial)

    try:
        if cliente_existente:
            # ✅ Atualiza cliente existente para virar usuário
            cliente_existente.role_id = usuario.role_id
            cliente_existente.senha = hashed_password
            cliente_existente.ativo = False

            # ✅ Define tipo baseado no perfil
            if usuario.role_id == 1:
                cliente_existente.tipo = "admin"
            elif usuario.role_id == 2:
                cliente_existente.tipo = "agente"
            else:
                cliente_existente.tipo = "cliente"

            db.commit()
            db.refresh(cliente_existente)

            return {
                "mensagem": "Usuário criado com sucesso a partir de um cliente existente.",
                "usuario_id": cliente_existente.id,
                "nome": cliente_existente.nome,
                "email": cliente_existente.email
            }

        else:
            # ✅ Criar novo usuário (não existia nem como cliente)
            if usuario.role_id == 1:
                tipo_usuario = "admin"
            elif usuario.role_id == 2:
                tipo_usuario = "agente"
            else:
                tipo_usuario = "cliente"

            novo_usuario = User(
                nome=usuario.nome,
                email=usuario.email,
                cpf=usuario.cpf,
                senha=hashed_password,
                tipo=tipo_usuario,
                role_id=usuario.role_id,
                ativo=False
            )

            db.add(novo_usuario)
            db.commit()
            db.refresh(novo_usuario)

            return {
                "mensagem": "Usuário criado com sucesso.",
                "usuario_id": novo_usuario.id,
                "nome": novo_usuario.nome,
                "email": novo_usuario.email
            }

    except Exception as e:
        db.rollback()
        print("======== ERRO AO CRIAR USUÁRIO ========")
        print(f"Erro: {str(e)}")
        print("Payload recebido:", usuario.dict())
        print("=======================================")
        raise HTTPException(status_code=500, detail=f"Erro ao criar usuário: {str(e)}")

@router.patch("/usuarios/{usuario_id}/status")
def alterar_status_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario_logado: User = Depends(get_current_user_strict)
):
    usuario = db.query(User).filter(User.id == usuario_id).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    # ✅ Impedir que o próprio usuário desative a si mesmo
    if usuario.id == usuario_logado.id:
        raise HTTPException(status_code=403, detail="Você não pode alterar seu próprio status.")

    # ✅ Apenas Admin pode alterar status de outros usuários
    if usuario_logado.role.nome != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem alterar o status de usuários.")

    try:
        # ✅ Alternar o status
        usuario.ativo = not usuario.ativo
        db.commit()
        return {"mensagem": "Status do usuário alterado com sucesso.", "ativo": usuario.ativo}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao alterar status do usuário: {e}")
