from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Empresa as EmpresaModel
from app.schemas import EmpresaCreate, EmpresaOut

router = APIRouter(tags=["Empresa"])  # ✅ Prefixo removido

# GET - buscar empresa (assumindo que só há uma)
@router.get("/", response_model=EmpresaOut)
def get_empresa(db: Session = Depends(get_db)):
    empresa = db.query(EmpresaModel).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não cadastrada.")
    return empresa

# POST - criar nova empresa
@router.post("/", response_model=EmpresaOut)
def criar_empresa(dados: EmpresaCreate, db: Session = Depends(get_db)):
    if db.query(EmpresaModel).first():
        raise HTTPException(status_code=400, detail="Empresa já cadastrada. Use o método de atualização.")
    nova = EmpresaModel(**dados.dict())
    db.add(nova)
    db.commit()
    db.refresh(nova)
    return nova

# PUT - atualizar empresa (único registro)
@router.put("/", response_model=EmpresaOut)
def atualizar_empresa(dados: EmpresaCreate, db: Session = Depends(get_db)):
    empresa = db.query(EmpresaModel).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não cadastrada.")

    for campo, valor in dados.dict().items():
        setattr(empresa, campo, valor)

    db.commit()
    db.refresh(empresa)
    return empresa
