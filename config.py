# config.py

import os
from dotenv import load_dotenv

# 🔄 Carrega variáveis do .env
load_dotenv()

# 🔗 Configurações principais
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# 🔐 Configurações do sistema
API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")
COOKIE_SECRET = os.getenv("COOKIE_SECRET")

# 🔑 Asaas
ASAAS_API_KEY = os.getenv("ASAAS_API_KEY")
