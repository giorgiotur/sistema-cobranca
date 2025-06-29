from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
import os

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Pega a URL do banco de dados definida no .env
DATABASE_URL = os.getenv("DATABASE_URL")

# Cria a engine de conexão com o banco
engine = create_engine(DATABASE_URL)

# Cria a fábrica de sessões
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base que será herdada pelos modelos
Base = declarative_base()

# Função para injetar a sessão no FastAPI com Depends
def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
