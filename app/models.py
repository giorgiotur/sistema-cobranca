from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Float,
    Date,
    Text,
    DateTime,
    Boolean,
    func,
)
from sqlalchemy.orm import relationship
from app.database import Base
from sqlalchemy import Column, String, Text
import uuid
from app.database import Base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, JSON, ForeignKey
from datetime import datetime
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid


# =======================
# Tabela de Perfis (Role)
# =======================
class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)

    # Relacionamento com usuários
    usuarios = relationship("User", back_populates="role")


# =======================
# Tabela de Usuários
# =======================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    senha = Column(String, nullable=True)
    cpf = Column(String, unique=True, nullable=False)
    telefone = Column(String)
    tipo = Column(String, default="cliente")  # Cliente, Agente, Admin
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)
    id_asaas = Column(String, nullable=True)
    asaas_status = Column(String, default="pendente")
    ativo = Column(Boolean, default=True)

    # Endereço
    cep = Column(String)
    rua = Column(String)
    numero = Column(String)
    complemento = Column(String)
    bairro = Column(String)
    cidade = Column(String)
    estado = Column(String)

    # NOVO CAMPO: Data de Nascimento
    data_nascimento = Column(Date, nullable=True)

    # Relacionamentos
    role = relationship("Role", back_populates="usuarios")
    convites = relationship("ConviteUsuario", back_populates="usuario")

    # 👉 Você deve adicionar AQUI:
    reservas = relationship("Reserva", back_populates="pagante")

# =======================
# Tabela de Pacotes
# =======================
class Package(Base):
    __tablename__ = "pacotes"

    id = Column(Integer, primary_key=True, index=True)
    destino = Column(String, nullable=False)
    descricao = Column(String)
    valor_total = Column(Float, nullable=False)
    parcelas = Column(Integer, nullable=False)
    data_ida = Column(Date, nullable=False)
    data_volta = Column(Date, nullable=False)
    hotel = Column(String)
    voo = Column(String)
    nome_viajantes = Column(String)


# =======================
# Tabela de Logs de Integração
# =======================
class LogIntegracao(Base):
    __tablename__ = "log_integracao"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(50))  # Exemplo: 'asaas'
    status = Column(String(20))  # sucesso, erro
    mensagem = Column(Text)
    payload = Column(Text)
    resposta = Column(Text)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())


# =======================
# Tabela de Convites de Usuário
# =======================
class ConviteUsuario(Base):
    __tablename__ = "convites_usuarios"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    expira_em = Column(DateTime, nullable=False)
    usado_em = Column(DateTime, nullable=True)

    usuario = relationship("User", back_populates="convites")

class Hotel(Base):
    __tablename__ = "hoteis"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String, nullable=False)
    destino = Column(String, nullable=False)
    descricao = Column(Text, nullable=True)

class OrcamentoPrePago(Base):
    __tablename__ = "orcamentos_pre_pago"

    id = Column(Integer, primary_key=True, index=True)
    numero_orcamento = Column(Integer, unique=True, nullable=False)

    tipo_pacote = Column(String)
    destino = Column(String)
    data_ida = Column(Date)
    data_volta = Column(Date)
    numero_noites = Column(Integer)
    adultos = Column(Integer)
    chd_0_5 = Column(Integer)
    chd_6_11 = Column(Integer)
    cidade_hotel = Column(String)
    nome_hotel = Column(String)
    descricao_hotel = Column(Text)
    qtd_apartamentos = Column(Integer)
    acomodacao = Column(String)
    regime = Column(String)
    servicos = Column(Text)
    valor_total = Column(Float)
    prazo_cancelamento = Column(Date)
    parcelas_json = Column(JSON)
    data_criacao = Column(DateTime, server_default=func.now())
    descricao_parcelamento = Column(String)

    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by_user = relationship("User")

# =======================
# Tabela de rserva
# =======================
class Reserva(Base):
    __tablename__ = "reservas"

    id = Column(Integer, primary_key=True, index=True)
    numero_reserva_operadora = Column(String, nullable=False)
    observacoes = Column(String, nullable=True)
    pagante_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pagante_id_asaas = Column(String, nullable=True)
    parcelas_json = Column(JSON, nullable=True)
    id_cobranca_asaas = Column(String, nullable=True)
    status = Column(String, default="pendente")
    created_at = Column(DateTime, default=datetime.utcnow)
    operadora = Column(String, nullable=True)

    # 🔗 Relacionamentos
    pagante = relationship("User", back_populates="reservas")

    # 🔗 Relacionamento com orçamento
    orcamento_id = Column(Integer, ForeignKey("orcamentos_pre_pago.id"), nullable=True)
    orcamento = relationship("OrcamentoPrePago")

    # ✅ Relacionamento com passageiros
    passageiros = relationship("Passageiro", back_populates="reserva", cascade="all, delete-orphan")

class Passageiro(Base):
    __tablename__ = "passageiros"

    id = Column(Integer, primary_key=True, autoincrement=True)
    reserva_id = Column(Integer, ForeignKey("reservas.id"), nullable=False)
    primeiro_nome = Column(String, nullable=False)
    ultimo_nome = Column(String, nullable=False)
    cpf = Column(String, nullable=True)
    data_nascimento = Column(Date, nullable=True)

    reserva = relationship("Reserva", back_populates="passageiros")

# =======================
# empresa
# =======================

class Empresa(Base):
    __tablename__ = "empresas"

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