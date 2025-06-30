@echo off
setlocal enabledelayedexpansion
cls

echo 📦 Iniciando o sistema...

REM ===============================
REM 1. DETECTAR CAMINHO DO PROJETO
REM ===============================
set PROJETO_DIR=

if exist "C:\Users\AgenteRF03\Documents\sistema-cobranca" (
    set PROJETO_DIR=C:\Users\AgenteRF03\Documents\sistema-cobranca
) else if exist "C:\Users\Documents\sistema-cobranca" (
    set PROJETO_DIR=C:\Users\Documents\sistema-cobranca
)

if not defined PROJETO_DIR (
    echo ❌ Projeto não encontrado em nenhum caminho conhecido.
    pause
    exit /b
)

cd /d "!PROJETO_DIR!"
echo 📁 Projeto localizado em: !PROJETO_DIR!

REM ===============================
REM 2. GIT PULL (ATUALIZAR PROJETO)
REM ===============================
echo 🔄 Atualizando projeto com Git...
git pull

REM ===============================
REM 3. CRIAR VENV SE NAO EXISTIR
REM ===============================
if not exist "venv\" (
    echo ⚙️ Ambiente virtual não encontrado. Criando...
    python -m venv venv
)

REM ===============================
REM 4. ATIVAR VENV
REM ===============================
call "venv\Scripts\activate.bat"

REM ===============================
REM 5. ATUALIZAR PIP AUTOMATICAMENTE
REM ===============================
echo 🚀 Atualizando pip...
python -m pip install --upgrade pip

REM ===============================
REM 6. INSTALAR DEPENDÊNCIAS
REM ===============================
if exist "requirements.txt" (
    echo 📦 Instalando dependências do requirements.txt...
    pip install -r requirements.txt
) else (
    echo ⚠️ Arquivo requirements.txt não encontrado. Pulando instalação.
)

REM ===============================
REM 7. INICIAR FASTAPI E STREAMLIT
REM ===============================
start "FastAPI" cmd /k "cd /d !PROJETO_DIR! && call venv\\Scripts\\activate.bat && uvicorn app.main:app --reload"
start "Painel" cmd /k "cd /d !PROJETO_DIR! && call venv\\Scripts\\activate.bat && streamlit run painel.py"

REM ===============================
REM 8. COMMIT OPCIONAL AO FINAL
REM ===============================
echo.
set /p SALVAR=🔐 Deseja salvar as alterações no GitHub? (s para sim): 
if /I "!SALVAR!"=="s" (
    set /p COMMIT_MSG=💬 Digite a mensagem do commit: 
    if not "!COMMIT_MSG!"=="" (
        git add .
        git commit -m "!COMMIT_MSG!"
        git push
        echo ✅ Alterações enviadas com sucesso!
    ) else (
        echo ⚠️ Commit cancelado (mensagem em branco).
    )
) else (
    echo ℹ️ Alterações locais não foram enviadas para o GitHub.
)

pause


