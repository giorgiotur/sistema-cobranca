from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime
from typing import Optional
from typing import List, Optional
from sqlalchemy import Column, Integer, String
from app.database import Base
import uuid


# =====================
# ESQUEMAS PARA PERFIL (ROLE)
# =====================

class RoleBase(BaseModel):
    nome: str

class RoleCreate(RoleBase):
    pass

class RoleOut(RoleBase):
    id: int

    class Config:
        from_attributes = True

# =====================
# ESQUEMAS PARA USUÁRIO
# =====================

class UserCreate(BaseModel):
    nome: str
    cpf: str
    email: EmailStr
    role_id: int
    senha: Optional[str] = None  
    data_nascimento: Optional[date] = None

class UserOut(BaseModel):
    id: int
    nome: str
    cpf: Optional[str] = None
    email: str
    perfil: Optional[str]
    ativo: bool
    data_nascimento: Optional[date] = None

    cep: Optional[str] = None
    rua: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    telefone: Optional[str] = None

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    cpf: Optional[str] = None
    role_id: Optional[int] = None
    data_nascimento: Optional[date] = None

    cep: Optional[str] = None
    rua: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    telefone: Optional[str] = None

# =====================
# LOGIN / AUTENTICAÇÃO
# =====================

class LoginInput(BaseModel):
    email: EmailStr
    senha: str

class Token(BaseModel):
    access_token: str
    token_type: str
    nome: str
    perfil: str

# =====================
# PACOTES DE VIAGEM
# =====================

class PackageCreate(BaseModel):
    destino: str
    descricao: Optional[str] = None
    valor_total: float
    parcelas: int
    data_ida: date
    data_volta: date
    hotel: Optional[str] = None
    voo: Optional[str] = None
    nome_viajantes: Optional[str] = None

class PackageOut(PackageCreate):
    id: int

    class Config:
        from_attributes = True

# =====================
# OUTROS
# =====================

class ConviteOut(BaseModel):
    token: str
    expira_em: datetime

    class Config:
        orm_mode = True

class DefinirSenha(BaseModel):
    senha: str

class UserConvite(BaseModel):
    nome: str
    email: str
    cpf: str
    role_id: int

class HotelOut(BaseModel):
    id: uuid.UUID
    nome: str
    destino: str
    descricao: Optional[str]

    class Config:
        from_attributes = True

# =====================
# ORÇAMENTO PRÉ-PAGO
# =====================

class ParcelaPrePago(BaseModel):
    parcela: int
    vencimento: str
    valor: float

class OrcamentoPrePagoCreate(BaseModel):
    tipo_pacote: str
    destino: str
    data_ida: date
    data_volta: date
    numero_noites: int
    adultos: int
    chd_0_5: int
    chd_6_11: int
    cidade_hotel: str
    nome_hotel: str
    descricao_hotel: str
    qtd_apartamentos: int
    acomodacao: str
    regime: str
    servicos: str
    valor_total: float
    prazo_cancelamento: date
    parcelas_json: Optional[List[ParcelaPrePago]] = []
    descricao_parcelamento: Optional[str] = None

class OrcamentoPrePagoOut(OrcamentoPrePagoCreate):
    id: int
    numero_orcamento: int
    data_criacao: datetime
    parcelas_json: Optional[List[ParcelaPrePago]] = None

    class Config:
        from_attributes = True

# =====================
# reservas
# =====================
class PassageiroCreate(BaseModel):
    primeiro_nome: str
    ultimo_nome: str
    cpf: Optional[str]
    data_nascimento: Optional[date]


class ParcelaReserva(BaseModel):
    descricao: str
    valor: float
    vencimento: str
    parcela: Optional[int] = None


class ReservaCreate(BaseModel):
    numero_reserva_operadora: str
    observacoes: Optional[str] = None
    pagante_id: int
    pagante_id_asaas: Optional[str] = None
    parcelas_json: Optional[List[ParcelaReserva]] = None
    id_cobranca_asaas: Optional[str] = None
    status: Optional[str] = "pendente"
    orcamento_id: Optional[int] = None
    passageiros: Optional[List[PassageiroCreate]] = []
    operadora: Optional[str] = None

class ReservaOut(BaseModel):
    id: int
    numero_reserva_operadora: str
    observacoes: Optional[str]
    pagante_id: int
    pagante_id_asaas: Optional[str]
    parcelas_json: Optional[List[ParcelaReserva]]
    id_cobranca_asaas: Optional[str]
    status: Optional[str]
    created_at: datetime
    operadora: Optional[str] = None 
    orcamento: Optional[OrcamentoPrePagoOut] = None

    class Config:
        from_attributes = True

# =====================
# Empresa 
# =====================
class Empresa(Base):
    __tablename__ = "empresas"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    razao_social = Column(String, nullable=False)
    nome_fantasia = Column(String, nullable=False)
    cnpj = Column(String, nullable=True)
    cep = Column(String, nullable=True)
    logradouro = Column(String, nullable=True)
    numero = Column(String, nullable=True)
    bairro = Column(String, nullable=True)
    municipio = Column(String, nullable=True)
    uf = Column(String, nullable=True)
    telefone = Column(String, nullable=True)

class EmpresaBase(BaseModel):
    razao_social: str
    nome_fantasia: str
    cnpj: Optional[str] = None
    cep: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    bairro: Optional[str] = None
    municipio: Optional[str] = None
    uf: Optional[str] = None
    telefone: Optional[str] = None

class EmpresaCreate(EmpresaBase):
    pass

class EmpresaOut(EmpresaBase):
    id: int

    class Config:
        from_attributes = True
