from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/pacotes", tags=["Pacotes"])

# Criar um novo pacote
@router.post("/", response_model=schemas.PackageOut)
def criar_pacote(pacote: schemas.PackageCreate, db: Session = Depends(get_db)):
    novo_pacote = models.Package(**pacote.dict())
    db.add(novo_pacote)
    db.commit()
    db.refresh(novo_pacote)
    return novo_pacote

# Listar todos os pacotes
@router.get("/", response_model=List[schemas.PackageOut])
def listar_pacotes(db: Session = Depends(get_db)):
    return db.query(models.Package).all()
