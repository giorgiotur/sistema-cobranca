import requests
import os
from dotenv import load_dotenv
import json
from app.models import LogIntegracao
from sqlalchemy.orm import Session

load_dotenv()

AMBIENTE = os.getenv("AMBIENTE", "sandbox")

if AMBIENTE == "producao":
    ASAAS_API_URL = "https://www.asaas.com/api/v3"
else:
    ASAAS_API_URL = "https://sandbox.asaas.com/api/v3"

ASAAS_API_KEY = os.getenv("ASAAS_API_KEY")

# NOVO PARÂMETRO: external_reference na função criar_cobranca_individual
def criar_cobranca_individual(cliente_id: str, valor: float, vencimento: str, descricao: str, db: Session, external_reference: str = None):
    url = f"{ASAAS_API_URL}/payments"

    payload = {
        "customer": cliente_id,
        "billingType": "BOLETO",
        "value": valor,
        "dueDate": vencimento,
        "description": descricao,
        "notifyCustomer": False
    }

    # NOVO: incluir externalReference no payload, se fornecido
    if external_reference:
        payload["externalReference"] = external_reference

    headers = {
        "Content-Type": "application/json",
        "access_token": ASAAS_API_KEY
    }

    print(f"DEBUG - Enviando cobrança para URL: {url}")
    print(f"DEBUG - Payload: {payload}")

    response = requests.post(url, json=payload, headers=headers)

    print(f"DEBUG - Status Code: {response.status_code}")
    print(f"DEBUG - Response: {response.text}")

    try:
        log = LogIntegracao(
            tipo="asaas",
            status="sucesso" if response.status_code in [200, 201] else "erro",
            mensagem="Cobrança criada com sucesso" if response.status_code in [200, 201] else "Erro ao criar cobrança no Asaas",
            payload=json.dumps(payload, ensure_ascii=False),
            resposta=response.text
        )
        db.add(log)
        db.commit()
    except Exception as e:
        print(f"Erro ao salvar log de integração: {e}")
        db.rollback()

    if response.status_code in [200, 201]:
        resultado = response.json()
        return resultado.get("id")
    else:
        try:
            erro_json = response.json()
            if "errors" in erro_json and len(erro_json["errors"]) > 0:
                erro_codigo = erro_json["errors"][0].get("code")
                erro_descricao = erro_json["errors"][0].get("description")
                raise Exception(f"Erro Asaas [{erro_codigo}]: {erro_descricao}")
            else:
                raise Exception(f"Erro inesperado do Asaas: {response.text}")
        except Exception as e:
            raise Exception(f"Falha ao processar erro do Asaas: {e}")

# NOVO PARÂMETRO: external_reference na função criar_cobrancas_por_parcelas
def criar_cobrancas_por_parcelas(cliente_id: str, parcelas: list, db: Session, external_reference: str = None):
    parcelas_dict = []
    for parcela in parcelas:
        if hasattr(parcela, "dict"):
            parcelas_dict.append(parcela.dict())
        else:
            parcelas_dict.append(parcela)

    ids_cobrancas = []

    for idx, parcela in enumerate(parcelas_dict):
        try:
            descricao = f"Parcela {parcela.get('parcela')} - {parcela.get('descricao', 'Reserva')}"
            valor = float(parcela.get('valor'))
            vencimento = parcela.get('vencimento')

            if not vencimento:
                raise Exception(f"Parcela {idx + 1} está sem data de vencimento.")

            # NOVO: repassando external_reference
            id_cobranca = criar_cobranca_individual(
                cliente_id,
                valor,
                vencimento,
                descricao,
                db,
                external_reference  # Mantido como nova funcionalidade
            )
            ids_cobrancas.append(id_cobranca)

        except Exception as e:
            print(f"Erro ao criar parcela {idx + 1}: {e}")
            raise Exception(f"Falha ao criar parcela {idx + 1} no Asaas: {e}")

    return ids_cobrancas
