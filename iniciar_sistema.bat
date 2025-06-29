@echo off
echo 🔄 Ativando ambiente virtual...

cd /d "C:\Users\Samsung\Documents\sistema-cobranca"

call venv\Scripts\activate.bat

echo ✅ Ambiente virtual ativado.
echo 🚀 Iniciando Streamlit...

streamlit run painel.py
