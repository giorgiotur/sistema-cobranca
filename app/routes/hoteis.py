import os
import uuid
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from app.database import get_db
from app.models import Hotel
from app.schemas import HotelOut
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

router = APIRouter(
    prefix="/hoteis",
    tags=["Hoteis"]
)

# ✅ GET /hoteis - Buscar hotel por destino e nome (filtro flexível com ILIKE)
@router.get("/", response_model=HotelOut, response_model_exclude_none=True)
def buscar_hotel(destino: str = Query(...), nome: str = Query(...), db: Session = Depends(get_db)):
    hotel = db.query(Hotel).filter(
        Hotel.destino.ilike(f"%{destino}%"),
        Hotel.nome.ilike(f"%{nome}%")
    ).first()

    if not hotel:
        return JSONResponse(status_code=404, content={"detail": "Hotel não encontrado."})

    return hotel


# ✅ Schema para receber o texto original no POST
class TextoOriginalIn(BaseModel):
    texto_original: str

# ✅ POST /hoteis/gerar-descricao - Gera e salva a descrição usando texto original
@router.post("/gerar-descricao", response_model=HotelOut)
def gerar_descricao_hotel(
    nome: str = Query(...),
    destino: str = Query(...),
    payload: TextoOriginalIn = None,
    db: Session = Depends(get_db)
):
    # 1. Verificar se o hotel já existe com descrição
    hotel_existente = db.query(Hotel).filter(
        Hotel.destino == destino,
        Hotel.nome.ilike(f"%{nome}%")
    ).first()

    if hotel_existente and hotel_existente.descricao:
        return hotel_existente

    # 2. Verificar se o texto original foi enviado
    if not payload or not payload.texto_original.strip():
        raise HTTPException(status_code=400, detail="Texto original é obrigatório para geração da descrição.")

        # 3. Montar o prompt inteligente
    prompt = (
        "Você é um redator especializado em turismo. Reescreva o texto abaixo de forma comercial, objetiva e convidativa. "
        "Foque em destacar os principais atrativos e benefícios do hotel, transmitindo experiências positivas para o turista.\n\n"
        "❗️ Regras:\n"
        "- Máximo de 3 parágrafos curtos.\n"
        "- Limite total de até 700 caracteres (incluindo espaços).\n"
        "- Não adicione informações que não estejam no texto fornecido.\n"
        "- Evite iniciar o texto com expressões como: 'Descubra', 'Conheça', 'Desfrute', 'Explore' ou similares.\n"
        "- Prefira uma linguagem sensorial e envolvente, mas respeitando o limite de tamanho.\n\n"
        f"Texto original:\n{payload.texto_original}"
    )

    # 4. Chamada à OpenAI (IA)
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )
        descricao_gerada = response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar descrição via OpenAI API: {str(e)}")

    # 5. Salvar o hotel no banco
    novo_hotel = Hotel(
        id=uuid.uuid4(),
        nome=nome,
        destino=destino,
        descricao=descricao_gerada
    )
    db.add(novo_hotel)
    db.commit()
    db.refresh(novo_hotel)

    # 6. Retornar o hotel com a descrição gerada
    return novo_hotel

# ✅ GET /hoteis/destinos - Lista todos os destinos únicos
@router.get("/destinos")
def listar_destinos(db: Session = Depends(get_db)):
    destinos = db.query(Hotel.destino).distinct().all()
    return [d[0] for d in destinos if d[0]]
