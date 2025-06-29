from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from weasyprint import HTML
from datetime import datetime
from typing import List
import tempfile
import os
import json

from app.database import get_db
from app.models import Reserva, User, Empresa, Hotel
from app.schemas import ReservaCreate, ReservaOut
from app.auth import get_current_user_strict
from utils.integracao_asaas import criar_cobrancas_por_parcelas
from app.models import Passageiro 
from sqlalchemy.orm import joinedload

# 🔗 Roteador principal para reservas
router = APIRouter(prefix="/reservas", tags=["Reservas"])

# 📁 Diretório dos templates
templates = Jinja2Templates(directory="app/templates")


# =========================
# 🔸 Criar Reserva
# =========================
@router.post("/", response_model=ReservaOut, status_code=201)
def criar_reserva(
    reserva_dados: ReservaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_strict)
):
    try:
        cliente = db.query(User).filter(User.id == reserva_dados.pagante_id).first()
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente pagante não encontrado.")

        parcelas_json_str = json.dumps(
            [parcela.dict() if hasattr(parcela, 'dict') else parcela for parcela in reserva_dados.parcelas_json],
            ensure_ascii=False
        )

        nova_reserva = Reserva(
            numero_reserva_operadora=reserva_dados.numero_reserva_operadora,
            observacoes=reserva_dados.observacoes,
            pagante_id=reserva_dados.pagante_id,
            parcelas_json=parcelas_json_str,
            status="pendente",
            created_at=datetime.now(),
            orcamento_id=reserva_dados.orcamento_id,  # 
            operadora=reserva_dados.operadora 
        )
        db.add(nova_reserva)
        db.commit()
        db.refresh(nova_reserva)

        # ✅ Salvar passageiros vinculados à reserva
        for v in reserva_dados.passageiros:
            novo_passageiro = Passageiro(
                reserva_id=nova_reserva.id,
                primeiro_nome=v.primeiro_nome,
                ultimo_nome=v.ultimo_nome,
                cpf=v.cpf,
                data_nascimento=v.data_nascimento
            )
            db.add(novo_passageiro)
        db.commit()

        # ✅ Criar cobranças no Asaas
        try:
            ids_cobrancas = criar_cobrancas_por_parcelas(
                cliente.id_asaas,
                reserva_dados.parcelas_json,
                db,
                external_reference=str(nova_reserva.id)
            )
            nova_reserva.id_cobranca_asaas = ",".join(ids_cobrancas)
            nova_reserva.status = "cobranca_criada"
            db.commit()
        except Exception as e:
            nova_reserva.status = "erro_asaas"
            db.commit()
            raise HTTPException(status_code=500, detail=f"Erro ao criar cobrança no Asaas: {str(e)}")

        try:
            nova_reserva.parcelas_json = json.loads(nova_reserva.parcelas_json)
        except Exception:
            nova_reserva.parcelas_json = []

        return nova_reserva

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao criar reserva: {str(e)}")


# =========================
# 🔸 Listar Reservas
# =========================
@router.get("/", response_model=List[ReservaOut])
def listar_reservas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_strict)
):
    reservas = db.query(Reserva).all()
    for reserva in reservas:
        try:
            reserva.parcelas_json = json.loads(reserva.parcelas_json) if reserva.parcelas_json else []
        except Exception:
            reserva.parcelas_json = []
    return reservas


# =========================
# 🔸 Gerar Contrato (HTML ou PDF)
# =========================
@router.get("/{id}/contrato", response_class=HTMLResponse)
def contrato_reserva(
    request: Request,
    id: int,
    formato: str = Query(default="html", regex="^(html|pdf)$"),
    modo: str = Query(default="visualizar", regex="^(visualizar|imprimir)$"),  # 🔹 NOVO PARÂMETRO
    db: Session = Depends(get_db),
):
    reserva = db.query(Reserva).filter(Reserva.id == id).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva não encontrada")

    cliente = db.query(User).filter(User.id == reserva.pagante_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente da reserva não encontrado")

    empresa = db.query(Empresa).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não cadastrada")

    agente = db.query(User).filter(User.tipo == "agente").first()
    if not agente:
        agente = User(nome="Agente não encontrado")

    passageiros = getattr(reserva, "passageiros", [])

    # 🔧 CORREÇÃO: garantir que parcelas_json seja lista, mesmo se string
    import json
    try:
        parcelas = json.loads(reserva.parcelas_json) if isinstance(reserva.parcelas_json, str) else reserva.parcelas_json
    except Exception:
        parcelas = []

    pagamento = None
    if parcelas:
        pagamento = {
            "plano": reserva.orcamento.descricao_parcelamento if reserva.orcamento else "—",
            "valor_total": sum(p.get('valor', 0) for p in parcelas),
            "parcelas": [
                {
                    "numero": p.get("parcela", idx + 1),
                    "valor": p.get("valor", 0),
                    "vencimento": p.get("vencimento", "")
                }
                for idx, p in enumerate(parcelas)
            ],
        }

    context = {
        "request": request,
        "reserva": reserva,
        "cliente": {
            "nome": cliente.nome,
            "cpf": cliente.cpf,
            "data_nascimento": cliente.data_nascimento.strftime("%d/%m/%Y") if cliente.data_nascimento else "—",
            "telefone": cliente.telefone,
            "rua": cliente.rua,
            "numero": cliente.numero,
            "bairro": cliente.bairro,
            "complemento": cliente.complemento,
            "cidade": cliente.cidade,
            "estado": cliente.estado,
            "cep": cliente.cep,
        },
        "empresa": empresa,
        "agente": agente,
        "hoteis": [{
            "nome": reserva.orcamento.nome_hotel if reserva.orcamento else "—",
            "localizador": reserva.orcamento.numero_orcamento or "—",
            "destino": reserva.orcamento.destino if reserva.orcamento else "—",
            "checkin": reserva.orcamento.data_ida.strftime("%d/%m/%Y") if reserva.orcamento and reserva.orcamento.data_ida else "—",
            "checkout": reserva.orcamento.data_volta.strftime("%d/%m/%Y") if reserva.orcamento and reserva.orcamento.data_volta else "—",
            "acomodacao": reserva.orcamento.acomodacao if reserva.orcamento else "—",
            "regime": reserva.orcamento.regime if reserva.orcamento else "—",
        }] if reserva.orcamento else [],
        "passageiros": passageiros,
        "pagamento": pagamento,
        "data_extenso": reserva.created_at.strftime("%d de %B de %Y"),
        "horario": reserva.created_at.strftime("%H:%M:%S"),
        "modo": modo  # 🔹 repassa o modo para o template
    }

    # ✅ Filtro Jinja para datas reversas
    def reverse_date(value):
        try:
            parts = value.split("-")
            return f"{parts[2]}/{parts[1]}/{parts[0]}"
        except:
            return value
    templates.env.filters["reverse_date"] = reverse_date

    template_nome = "contrato_hospedagem_imprimir.html" if modo == "imprimir" else "contrato_hospedagem.html"
    html_content = templates.get_template(template_nome).render(context)

    if formato == "pdf":
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            HTML(string=html_content).write_pdf(tmp_pdf.name)
            tmp_pdf.seek(0)
            pdf_data = tmp_pdf.read()
        os.unlink(tmp_pdf.name)
        return Response(content=pdf_data, media_type="application/pdf")

    return HTMLResponse(content=html_content)


@router.get("/por-cliente/{cliente_id}", response_model=list[ReservaOut])
def listar_reservas_por_cliente(cliente_id: int, db: Session = Depends(get_db)):
    reservas = (
        db.query(Reserva)
        .options(joinedload(Reserva.orcamento))  # carrega relacionamento com orçamento
        .filter(Reserva.pagante_id == cliente_id)
        .all()
    )

    if not reservas:
        raise HTTPException(status_code=404, detail="Nenhuma reserva encontrada para este cliente.")

    import json
    for reserva in reservas:
        try:
            if isinstance(reserva.parcelas_json, str):
                reserva.parcelas_json = json.loads(reserva.parcelas_json)
        except Exception:
            reserva.parcelas_json = []

    # ✅ conversão manual para garantir que todos os campos (inclusive operadora) sejam incluídos
    return [ReservaOut.from_orm(reserva) for reserva in reservas]

@router.get("/por-orcamento/{orcamento_id}", response_model=list[ReservaOut])
def listar_reservas_por_orcamento(orcamento_id: int, db: Session = Depends(get_db)):
    reservas = (
        db.query(Reserva)
        .filter(Reserva.orcamento_id == orcamento_id)
        .all()
    )

    if not reservas:
        return []

    import json
    for reserva in reservas:
        try:
            if isinstance(reserva.parcelas_json, str):
                reserva.parcelas_json = json.loads(reserva.parcelas_json)
        except Exception:
            reserva.parcelas_json = []

    return [ReservaOut.from_orm(reserva) for reserva in reservas]
