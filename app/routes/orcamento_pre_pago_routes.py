from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app import models, schemas
from app.models import User, OrcamentoPrePago
from typing import List, Optional
from datetime import datetime
from app.auth import get_current_user_strict
from app.auth import get_current_user_flex
from fastapi.responses import StreamingResponse
from io import BytesIO
from jinja2 import Environment, FileSystemLoader
from app.schemas import OrcamentoPrePagoOut
from utils import parcelamento
from datetime import date
import os
import json

# Configurar o ambiente Jinja2 para templates
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

templates_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# =======================
# Endpoint GET - HTML do Orçamento
# =======================
@router.get("/{id}/html", response_class=HTMLResponse)
def renderizar_orcamento_html(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_flex)
):
    orcamento = db.query(models.OrcamentoPrePago).filter(models.OrcamentoPrePago.id == id).first()
    if not orcamento:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado.")

    nome_cliente = "Cliente Teste"
    nome_usuario = current_user.nome

    hoteis = [{
        "nome": orcamento.nome_hotel or "",
        "descricao": orcamento.descricao_hotel or "",
        "valor": f"R$ {orcamento.valor_total:.2f}".replace('.', ',') if orcamento.valor_total else "R$ 0,00",
        "data_entrada": orcamento.data_ida.strftime("%d/%m/%Y") if orcamento.data_ida else "",
        "data_saida": orcamento.data_volta.strftime("%d/%m/%Y") if orcamento.data_volta else "",
        "regime": orcamento.regime or "",
        "tipo_apto": orcamento.acomodacao or "",
        "numero_apto": orcamento.qtd_apartamentos or 1,
        "servicos": orcamento.servicos or ""
    }]

    parcelas = []
    if orcamento.parcelas_json:
        for parcela in orcamento.parcelas_json:
            if hasattr(parcela, "dict"):
                parcela_dict = parcela.dict()
            else:
                parcela_dict = parcela

            numero_parcela = parcela_dict.get('parcela')
            vencimento = parcela_dict.get('vencimento')
            valor = parcela_dict.get('valor', 0)
            descricao = parcela_dict.get('descricao', '')

            # ✅ Se não tiver descrição, monta usando parcela e vencimento
            if not descricao and numero_parcela and vencimento:
                descricao = f"Parcela {numero_parcela} - Vencto: {vencimento}"

            parcelas.append({
                "descricao": descricao,
                "valor": float(valor)
            })

    context = {
        "request": request,
        "cidade_destino": orcamento.destino or "",
        "adultos": orcamento.adultos,
        "chd_0_5": orcamento.chd_0_5,
        "chd_6_11": orcamento.chd_6_11,
        "numero_noites": orcamento.numero_noites,
        "nome_cliente": nome_cliente,
        "data_orcamento": orcamento.data_criacao.strftime("%d/%m/%Y %H:%M") if orcamento.data_criacao else "",
        "numero_orcamento": orcamento.numero_orcamento,
        "hoteis": hoteis,
        "parcelas": parcelas,
        "data_cotacao": orcamento.data_criacao.strftime("%d/%m/%Y") if orcamento.data_criacao else "",
        "mensagem_taxa_primeira_parcela": "",
        "cidade_saida": orcamento.cidade_hotel or "",
        "nome_usuario": nome_usuario,
        "foto_usuario": "",
        "data_hora_geracao": orcamento.data_criacao.strftime("%d/%m/%Y %H:%M") if orcamento.data_criacao else "",
        "descricao_pagamento": orcamento.descricao_parcelamento,
    }

    return templates.TemplateResponse("orcamento_hospedagem_pre_pago.html", context)


# =======================
# Endpoint GET - Listagem de Orçamentos
# =======================
@router.get("/", response_model=dict)
def listar_orcamentos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_strict),
    data_inicio: Optional[datetime] = Query(None),
    data_fim: Optional[datetime] = Query(None),
    destino: Optional[str] = Query(None),
    numero_orcamento: Optional[int] = Query(None),
    agente: Optional[str] = Query(None),
    limit: int = 10,
    page: int = 1,
):
    query = db.query(OrcamentoPrePago).options(joinedload(OrcamentoPrePago.created_by_user))

    # Filtro por perfil
    if current_user.role.nome.lower() == "agente":
        query = query.filter(OrcamentoPrePago.created_by_user_id == current_user.id)

    # Filtros opcionais
    if data_inicio:
        query = query.filter(OrcamentoPrePago.data_criacao >= data_inicio)
    if data_fim:
        query = query.filter(OrcamentoPrePago.data_criacao <= data_fim)
    if destino:
        query = query.filter(OrcamentoPrePago.destino.ilike(f"%{destino}%"))
    if numero_orcamento:
        query = query.filter(OrcamentoPrePago.numero_orcamento == numero_orcamento)
    if agente:
        query = query.join(OrcamentoPrePago.created_by_user).filter(User.nome.ilike(f"%{agente}%"))

    total_registros = query.count()
    total_paginas = (total_registros + limit - 1) // limit
    offset = (page - 1) * limit

    orcamentos = (
        query.order_by(OrcamentoPrePago.data_criacao.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    resultado = []
    for orc in orcamentos:
        resultado.append({
            "id": orc.id,
            "numero_orcamento": orc.numero_orcamento,
            "destino": orc.destino,
            "data_ida": orc.data_ida,
            "data_volta": orc.data_volta,
            "nome_hotel": orc.nome_hotel,
            "valor_total": orc.valor_total,
            "data_criacao": orc.data_criacao,
            "agente": orc.created_by_user.nome if orc.created_by_user else "—"
        })

    return {
        "total_paginas": total_paginas,
        "pagina_atual": page,
        "total_registros": total_registros,
        "orcamentos": resultado,
    }

# =======================
# Endpoint POST - Criar Orçamento
# =======================
@router.post("/", status_code=status.HTTP_201_CREATED)
def criar_orcamento_pre_pago(
    orcamento: schemas.OrcamentoPrePagoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_strict)
):
    try:
        ultimo_orcamento = db.query(models.OrcamentoPrePago).order_by(models.OrcamentoPrePago.numero_orcamento.desc()).first()
        novo_numero = (ultimo_orcamento.numero_orcamento + 1) if ultimo_orcamento else 1

        parcelas = []
        if orcamento.parcelas_json:
            for parcela in orcamento.parcelas_json:
                if hasattr(parcela, "dict"):
                    parcela_dict = parcela.dict()
                else:
                    parcela_dict = parcela

                parcelas.append({
                    "parcela": parcela_dict.get('parcela'),
                    "vencimento": parcela_dict.get('vencimento'),
                    "valor": float(parcela_dict.get('valor', 0)),
                    "descricao": f"Parcela {parcela_dict.get('parcela', '')} - Vencto: {parcela_dict.get('vencimento', '')}"
                })

        novo_orcamento = models.OrcamentoPrePago(
            numero_orcamento=novo_numero,
            tipo_pacote=orcamento.tipo_pacote,
            destino=orcamento.destino,
            data_ida=orcamento.data_ida,
            data_volta=orcamento.data_volta,
            numero_noites=orcamento.numero_noites,
            adultos=orcamento.adultos,
            chd_0_5=orcamento.chd_0_5,
            chd_6_11=orcamento.chd_6_11,
            cidade_hotel=orcamento.cidade_hotel,
            nome_hotel=orcamento.nome_hotel,
            descricao_hotel=orcamento.descricao_hotel,
            qtd_apartamentos=orcamento.qtd_apartamentos,
            acomodacao=orcamento.acomodacao,
            regime=orcamento.regime,
            servicos=orcamento.servicos,
            valor_total=orcamento.valor_total,
            prazo_cancelamento=orcamento.prazo_cancelamento,
            parcelas_json=parcelas,
            descricao_parcelamento=orcamento.descricao_parcelamento,
            created_by_user_id=current_user.id
        )

        db.add(novo_orcamento)
        db.commit()
        db.refresh(novo_orcamento)

        return {
            "mensagem": "Orçamento criado com sucesso!",
            "id": novo_orcamento.id,
            "numero_orcamento": novo_orcamento.numero_orcamento
        }

    except Exception as e:
        db.rollback()
        print(f"ERRO AO CRIAR ORÇAMENTO >>> {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao criar orçamento: {e}")


# =======================
# Endpoint GET - Criar pdf e imprimir
# =======================
import os
from io import BytesIO
from fastapi.responses import FileResponse, StreamingResponse
from weasyprint import HTML

@router.get("/{id}/pdf", response_class=StreamingResponse)
def gerar_pdf_orcamento(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_flex)
):
    # Caminho onde os PDFs serão salvos
    pasta_pdf = "./app/static/pdfs/"
    os.makedirs(pasta_pdf, exist_ok=True)
    caminho_pdf = os.path.join(pasta_pdf, f"orcamento_{id}.pdf")

    # Se o PDF já existe, retorna direto o arquivo
    if os.path.exists(caminho_pdf):
        return FileResponse(
            caminho_pdf,
            media_type="application/pdf",
            filename=f"orcamento_{id}.pdf"
        )

    # Buscar orçamento
    orcamento = db.query(models.OrcamentoPrePago).filter(models.OrcamentoPrePago.id == id).first()
    if not orcamento:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado.")

    nome_cliente = "Cliente Teste"
    nome_usuario = current_user.nome

    hoteis = [{
        "nome": orcamento.nome_hotel or "",
        "descricao": orcamento.descricao_hotel or "",
        "valor": f"R$ {orcamento.valor_total:.2f}".replace('.', ',') if orcamento.valor_total else "R$ 0,00",
        "data_entrada": orcamento.data_ida.strftime("%d/%m/%Y") if orcamento.data_ida else "",
        "data_saida": orcamento.data_volta.strftime("%d/%m/%Y") if orcamento.data_volta else "",
        "regime": orcamento.regime or "",
        "tipo_apto": orcamento.acomodacao or "",
        "numero_apto": orcamento.qtd_apartamentos or 1,
        "servicos": orcamento.servicos or ""
    }]

    parcelas = []
    if orcamento.parcelas_json:
        for parcela in orcamento.parcelas_json:
            if hasattr(parcela, "dict"):
                parcela_dict = parcela.dict()
            else:
                parcela_dict = parcela

            parcelas.append({
                "descricao": parcela_dict.get("descricao", ""),
                "valor": float(parcela_dict.get("valor", 0))
            })

    context = {
        "cidade_destino": orcamento.destino or "",
        "adultos": orcamento.adultos,
        "chd_0_5": orcamento.chd_0_5,
        "chd_6_11": orcamento.chd_6_11,
        "numero_noites": orcamento.numero_noites,
        "data_checkin": orcamento.data_ida.strftime("%d/%m/%Y") if orcamento.data_ida else "",
        "data_checkout": orcamento.data_volta.strftime("%d/%m/%Y") if orcamento.data_volta else "",
        "nome_cliente": nome_cliente,
        "data_orcamento": orcamento.data_criacao.strftime("%d/%m/%Y %H:%M") if orcamento.data_criacao else "",
        "numero_orcamento": orcamento.numero_orcamento,
        "hoteis": hoteis,
        "parcelas": parcelas,
        "data_cotacao": orcamento.data_criacao.strftime("%d/%m/%Y") if orcamento.data_criacao else "",
        "mensagem_taxa_primeira_parcela": "",
        "cidade_saida": orcamento.cidade_hotel or "",
        "nome_usuario": nome_usuario,
        "foto_usuario": "",
        "data_hora_geracao": orcamento.data_criacao.strftime("%d/%m/%Y %H:%M") if orcamento.data_criacao else "",
        "descricao_pagamento": orcamento.descricao_parcelamento,
    }

    # Renderizar o HTML
    html_content = templates_env.get_template("orcamento_hospedagem_pre_pago.html").render(**context)

    # Gerar PDF
    pdf_file = BytesIO()
    base_url = str(request.url_for("renderizar_orcamento_html", id=id))
    HTML(string=html_content, base_url=base_url).write_pdf(target=pdf_file)
    pdf_file.seek(0)

    # Salvar o PDF no disco
    with open(caminho_pdf, "wb") as f:
        f.write(pdf_file.read())
    pdf_file.seek(0)

    # Retornar o PDF gerado
    return StreamingResponse(
        pdf_file,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=orcamento_{id}.pdf"}
    )

@router.get("/{id}", response_model=dict)
def buscar_orcamento_pre_pago_por_id(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_strict)
):
    orcamento = db.query(OrcamentoPrePago).filter(OrcamentoPrePago.id == id).first()

    if not orcamento:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado.")

    return {
        "id": orcamento.id,
        "numero_orcamento": orcamento.numero_orcamento,  
        "destino": orcamento.destino,
        "nome_hotel": orcamento.nome_hotel,
        "data_ida": orcamento.data_ida,
        "data_volta": orcamento.data_volta,
        "valor_total": orcamento.valor_total,
        "descricao_parcelamento": orcamento.descricao_parcelamento,
        "prazo_cancelamento": orcamento.prazo_cancelamento,
        "adultos": orcamento.adultos,
        "chd_0_5": orcamento.chd_0_5,
        "chd_6_11": orcamento.chd_6_11,
        "regime": orcamento.regime,
        "acomodacao": orcamento.acomodacao,
        "parcelas_json": orcamento.parcelas_json if orcamento.parcelas_json else [],
    }

@router.put("/{id}/recalcular-parcelamento", status_code=200)
def recalcular_parcelamento_orcamento(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_strict)
):
    orcamento = db.query(models.OrcamentoPrePago).filter(models.OrcamentoPrePago.id == id).first()
    if not orcamento:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado.")

    if not orcamento.data_ida or not orcamento.valor_total:
        raise HTTPException(status_code=400, detail="Data de ida e valor total são obrigatórios para recalcular o parcelamento.")

    # ✅ Trava: Se o orçamento foi criado hoje, não recalcula
    if orcamento.data_criacao and orcamento.data_criacao.date() == date.today():
        return {
            "mensagem": "Orçamento criado hoje. Recalculo de parcelamento não é necessário.",
            "parcelas": orcamento.parcelas_json,
            "descricao_parcelamento": orcamento.descricao_parcelamento
        }

    try:
        resultado = parcelamento.calcular_parcelamento(orcamento.data_ida, orcamento.valor_total)

        novas_parcelas = []
        for p in resultado["parcelas"]:
            novas_parcelas.append({
                "parcela": p.get("parcela"),
                "vencimento": p.get("vencimento"),
                "valor": p.get("valor"),
                "descricao": f"Parcela {p.get('parcela')} - Vencto: {p.get('vencimento')}"
            })

        orcamento.parcelas_json = novas_parcelas
        orcamento.descricao_parcelamento = resultado.get("mensagem", "")

        # ✅ Atualiza a data de criação para o momento atual
        orcamento.data_criacao = datetime.now()

        db.commit()
        db.refresh(orcamento)

        return {
            "mensagem": "Parcelamento recalculado com sucesso!",
            "parcelas": novas_parcelas,
            "descricao_parcelamento": orcamento.descricao_parcelamento
        }

    except Exception as e:
        db.rollback()
        print(f"Erro ao recalcular parcelamento: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao recalcular parcelamento: {e}")
from fastapi import status

@router.delete("/{id}", status_code=status.HTTP_200_OK)
def excluir_orcamento_pre_pago(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_strict)
):
    # Permitir apenas Admin
    if current_user.role.nome != "admin":
        raise HTTPException(status_code=403, detail="Apenas usuários admin podem excluir orçamentos.")

    orcamento = db.query(models.OrcamentoPrePago).filter(models.OrcamentoPrePago.id == id).first()
    if not orcamento:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado.")

    try:
        db.delete(orcamento)
        db.commit()
        return {"mensagem": "Orçamento excluído com sucesso!"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao excluir orçamento: {e}")

@router.get("/{id}/cpf", response_model=dict)
def obter_cpf_por_orcamento(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_strict)
):
    # Buscar reserva vinculada ao orçamento
    reserva = db.query(models.Reserva).filter(models.Reserva.orcamento_id == id).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva não encontrada para este orçamento.")

    cliente = reserva.pagante
    if not cliente or not cliente.cpf:
        raise HTTPException(status_code=404, detail="CPF do cliente não encontrado.")

    return {"cpf": cliente.cpf}
