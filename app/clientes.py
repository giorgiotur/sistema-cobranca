import os
import json
import re
import traceback
import requests
from dotenv import load_dotenv

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.database import get_db
from app.models import User, LogIntegracao, Package
from app.auth import get_current_user_strict
from typing import Optional
from datetime import date
from datetime import datetime, date



load_dotenv()
router = APIRouter()
ASAAS_API_KEY = os.getenv("ASAAS_API_KEY")

class ClienteCreate(BaseModel):
    nome: str
    email: EmailStr
    cpf: str
    telefone: str
    cep: str
    rua: str
    numero: str
    complemento: str = ""
    bairro: str
    cidade: str
    estado: str
    data_nascimento: Optional[date] = None

# ✅ Criar cliente
@router.post("/clientes/")
def criar_cliente(cliente: ClienteCreate, db: Session = Depends(get_db)):
    # ✅ Verificar duplicidade de CPF e E-mail
    if db.query(User).filter(User.cpf == cliente.cpf).first():
        raise HTTPException(status_code=400, detail="Cliente já cadastrado.")
    if db.query(User).filter(User.email == cliente.email).first():
        raise HTTPException(status_code=400, detail="E-mail já cadastrado.")

    # ✅ Criar cliente SEM role_id, SEM senha e SEM ativo=True
    novo_cliente = User(
        nome=cliente.nome,
        email=cliente.email,
        cpf=cliente.cpf,
        telefone=cliente.telefone,
        cep=cliente.cep,
        rua=cliente.rua,
        numero=cliente.numero,
        complemento=cliente.complemento,
        bairro=cliente.bairro,
        cidade=cliente.cidade,
        estado=cliente.estado,
        data_nascimento=cliente.data_nascimento,
        tipo="cliente",
        asaas_status="pendente",
        role_id=None,
        senha=None,
        ativo=False
    )

    try:
        db.add(novo_cliente)
        db.commit()
        db.refresh(novo_cliente)
    except Exception:
        db.rollback()
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Erro ao salvar cliente no banco.")

    # ✅ Integração com Asaas
    try:
        response = requests.post(
            "https://sandbox.asaas.com/api/v3/customers",
            headers={
                "accept": "application/json",
                "Content-Type": "application/json",
                "access_token": ASAAS_API_KEY,
            },
            json={
                "name": cliente.nome,
                "cpfCnpj": cliente.cpf,
                "email": cliente.email,
                "phone": cliente.telefone,
                "postalCode": cliente.cep,
                "address": cliente.rua,
                "addressNumber": cliente.numero,
                "complement": cliente.complemento,
                "province": cliente.bairro,
                "city": cliente.cidade,
                "state": cliente.estado,
                "notificationDisabled": True,
                "emailNotification": False,
                "smsNotification": False,
                "phoneCallNotification": False,
                "postalNotification": False
            }
        )

        if response.status_code != 200:
            raise Exception(f"Asaas erro: {response.status_code} - {response.text}")

        dados_asaas = response.json()
        novo_cliente.id_asaas = dados_asaas.get("id")
        novo_cliente.asaas_status = "sucesso"
        db.commit()

        db.add(LogIntegracao(
            tipo="asaas",
            status="sucesso",
            mensagem="Cliente criado com sucesso no Asaas",
            payload=cliente.model_dump_json(ensure_ascii=False),
            resposta=response.text
        ))
        db.commit()

    except Exception as e:
        db.rollback()
        novo_cliente.asaas_status = "erro"
        db.add(novo_cliente)

        db.add(LogIntegracao(
            tipo="asaas",
            status="erro",
            mensagem="Erro ao integrar com Asaas",
            payload=cliente.model_dump_json(ensure_ascii=False),
            resposta=str(e)
        ))
        db.commit()
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Cliente salvo local, mas falha no Asaas.")

    return {
        "mensagem": "Cliente cadastrado com sucesso!",
        "id": novo_cliente.id,
        "id_asaas": novo_cliente.id_asaas
    }


# ✅ Verificar CPF ou E-mail existente
@router.get("/clientes/verificar/")
def verificar_existencia(cpf: str = "", email: str = "", db: Session = Depends(get_db)):
    resultado = {"cpf": False, "email": False}

    if cpf:
        resultado["cpf"] = db.query(User).filter(User.cpf == cpf).first() is not None
    if email:
        resultado["email"] = db.query(User).filter(User.email == email).first() is not None

    return resultado

# ✅ Buscar cliente por CPF
@router.get("/clientes/por-cpf-ou-email/{termo}")
def buscar_cliente_por_cpf_ou_email_completo(termo: str, db: Session = Depends(get_db)):
    termo_limpo = re.sub(r'\D', '', termo)

    clientes = db.query(User).all()

    # Buscar por CPF
    cliente = next(
        (c for c in clientes if re.sub(r'\D', '', c.cpf or "") == termo_limpo),
        None
    )

    # Se não achar por CPF, tenta por E-mail
    if not cliente and "@" in termo:
        cliente = next(
            (c for c in clientes if c.email and termo.lower() in c.email.lower()),
            None
        )

    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    usuario = db.query(User).filter(User.cpf == cliente.cpf, User.role_id.isnot(None)).first()
    pacote = db.query(Package).filter(Package.nome_viajantes.contains(cliente.nome)).first()
    hospedagem = None  # Ajuste se tiver tabela hospedagem

    return {
        "id": cliente.id,
        "nome": cliente.nome,
        "cpf": cliente.cpf,
        "telefone": cliente.telefone,
        "asaas_status": cliente.asaas_status,
        "email": cliente.email,
        "cep": cliente.cep,
        "rua": cliente.rua,
        "numero": cliente.numero,
        "complemento": cliente.complemento,
        "bairro": cliente.bairro,
        "cidade": cliente.cidade,
        "estado": cliente.estado,
        "role_id": cliente.role_id,
        "data_nascimento": cliente.data_nascimento,
        "pacote_contratado": bool(pacote),
        "hospedagem_contratada": bool(hospedagem)
    }



# ✅ Novo Endpoint: Buscar por CPF, E-mail ou Nome
@router.get("/clientes/por-cpf-ou-email-ou-nome/{busca}")
def buscar_cliente_por_cpf_ou_email_ou_nome(
    busca: str,
    db: Session = Depends(get_db),
    usuario_logado: dict = Depends(get_current_user_strict),
):
    busca_normalizado = busca.replace('.', '').replace('-', '').replace(' ', '')

    try:
        cliente = db.query(User).filter(
            or_(
                func.replace(func.replace(func.replace(User.cpf, '.', ''), '-', ''), ' ', '') == busca_normalizado,
                User.email == busca,
                User.nome.ilike(f"%{busca}%")
            )
        ).first()

        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado.")

        # ✅ Se o cliente já for usuário (já tem role_id preenchido)
        if cliente.role_id:
            raise HTTPException(status_code=400, detail="Este cliente já possui acesso ao sistema como usuário.")

        # ✅ Se for cliente puro, retorna os dados
        return {
            "id": cliente.id,
            "nome": cliente.nome,
            "email": cliente.email,
            "cpf": cliente.cpf,
            "telefone": cliente.telefone,
            "role_id": cliente.role_id,
        }

    except HTTPException:
        raise  # Repassa os erros HTTP intencionais
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar cliente: {str(e)}")


# ✅ Reprocessar cliente
@router.post("/clientes/reprocessar/{cliente_id}")
def reprocessar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(User).filter(User.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    if cliente.asaas_status == "sucesso":
        raise HTTPException(status_code=400, detail="Cliente já integrado com sucesso.")

    try:
        response = requests.post(
            "https://sandbox.asaas.com/api/v3/customers",
            headers={
                "accept": "application/json",
                "Content-Type": "application/json",
                "access_token": ASAAS_API_KEY,
            },
            json={
                "name": cliente.nome,
                "cpfCnpj": cliente.cpf,
                "email": cliente.email,
                "phone": cliente.telefone,
                "postalCode": cliente.cep,
                "address": cliente.rua,
                "addressNumber": cliente.numero,
                "complement": cliente.complemento,
                "province": cliente.bairro,
                "city": cliente.cidade,
                "state": cliente.estado,
                "notificationDisabled": True,
                "emailNotification": False,
                "smsNotification": False,
                "phoneCallNotification": False,
                "postalNotification": False
            }
        )

        if response.status_code != 200:
            raise Exception(f"Asaas erro: {response.status_code} - {response.text}")

        dados_asaas = response.json()
        cliente.id_asaas = dados_asaas.get("id")
        cliente.asaas_status = "sucesso"

        log = LogIntegracao(
            tipo="asaas",
            status="sucesso",
            mensagem="Reprocessamento concluído",
            payload=json.dumps(dados_asaas, ensure_ascii=False),
            resposta=response.text
        )
        db.add(log)
        db.commit()

        return {"mensagem": "Cliente reenviado com sucesso."}

    except Exception as e:
        cliente.asaas_status = "erro"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Erro ao reprocessar: {str(e)}")

# ✅ Atualizar cliente
@router.put("/clientes/{id}")
def atualizar_cliente(id: int, cliente: dict, db: Session = Depends(get_db)):
    cliente_db = db.query(User).filter(User.id == id).first()
    if not cliente_db:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    for campo, valor in cliente.items():
        if hasattr(cliente_db, campo):
            if campo == "data_nascimento" and isinstance(valor, str):
                try:
                    valor = datetime.strptime(valor, "%Y-%m-%d").date()
                except Exception:
                    continue  # Ignora se a data vier com formato inválido
            setattr(cliente_db, campo, valor)

    try:
        db.commit()
        return {"mensagem": "Cliente atualizado com sucesso"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar cliente: {str(e)}")

@router.get("/clientes/{id}")
def buscar_cliente_por_id(id: int, db: Session = Depends(get_db)):
    cliente = db.query(User).filter(User.id == id).first()

    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    return {
        "id": cliente.id,
        "nome": cliente.nome,
        "cpf": cliente.cpf,
        "telefone": cliente.telefone,
        "email": cliente.email,
        "cep": cliente.cep,
        "rua": cliente.rua,
        "numero": cliente.numero,
        "complemento": cliente.complemento,
        "bairro": cliente.bairro,
        "cidade": cliente.cidade,
        "estado": cliente.estado,
        "asaas_status": cliente.asaas_status,
        "role_id": cliente.role_id,
        "data_nascimento": cliente.data_nascimento.isoformat() if cliente.data_nascimento else None

    }

@router.patch("/clientes/{id}/reprocessar-status-asaas")
def reprocessar_status_asaas(id: int, db: Session = Depends(get_db)):
    cliente = db.query(User).filter(User.id == id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    if cliente.asaas_status == "sucesso":
        raise HTTPException(status_code=400, detail="Cliente já integrado com sucesso.")

    try:
        response = requests.post(
            "https://sandbox.asaas.com/api/v3/customers",
            headers={
                "accept": "application/json",
                "Content-Type": "application/json",
                "access_token": ASAAS_API_KEY,
            },
            json={
                "name": cliente.nome,
                "cpfCnpj": cliente.cpf,
                "email": cliente.email,
                "phone": cliente.telefone,
                "postalCode": cliente.cep,
                "address": cliente.rua,
                "addressNumber": cliente.numero,
                "complement": cliente.complemento,
                "province": cliente.bairro,
                "city": cliente.cidade,
                "state": cliente.estado,
                "notificationDisabled": True,
                "emailNotification": False,
                "smsNotification": False,
                "phoneCallNotification": False,
                "postalNotification": False
            }
        )

        if response.status_code != 200:
            raise Exception(f"Asaas erro: {response.status_code} - {response.text}")

        dados_asaas = response.json()
        cliente.id_asaas = dados_asaas.get("id")
        cliente.asaas_status = "sucesso"

        log = LogIntegracao(
            tipo="asaas",
            status="sucesso",
            mensagem="Reprocessamento concluído (status Asaas)",
            payload=json.dumps(dados_asaas, ensure_ascii=False),
            resposta=response.text
        )
        db.add(log)
        db.commit()

        return {"mensagem": "Status Asaas reprocessado com sucesso."}

    except Exception as e:
        cliente.asaas_status = "erro"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Erro ao reprocessar status Asaas: {str(e)}")



@router.get("/clientes/por-cpf/{cpf}")
def buscar_cliente_por_cpf(cpf: str, db: Session = Depends(get_db)):
    cpf_limpo = re.sub(r'\D', '', cpf)

    cliente = db.query(User).filter(
        func.replace(func.replace(func.replace(User.cpf, '.', ''), '-', ''), ' ', '') == cpf_limpo
    ).first()

    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    return {
        "id": cliente.id,
        "nome": cliente.nome,
        "cpf": cliente.cpf,
        "telefone": cliente.telefone,
        "email": cliente.email,
        "cep": cliente.cep,
        "rua": cliente.rua,
        "numero": cliente.numero,
        "complemento": cliente.complemento,
        "bairro": cliente.bairro,
        "cidade": cliente.cidade,
        "estado": cliente.estado,
        "asaas_status": cliente.asaas_status,
        "id_asaas": cliente.id_asaas,
        "role_id": cliente.role_id,
        "tipo": cliente.tipo,
        "ativo": cliente.ativo,
        "data_nascimento": cliente.data_nascimento.isoformat() if cliente.data_nascimento else None
    }