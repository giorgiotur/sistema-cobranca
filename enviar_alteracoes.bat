@echo off
setlocal enabledelayedexpansion
cls

echo 🚀 Enviando alterações para o GitHub...

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
REM 2. VERIFICAR ALTERAÇÕES
REM ===============================
echo 🔍 Verificando alterações locais...
git status

REM ===============================
REM 3. SOLICITAR MENSAGEM DO COMMIT
REM ===============================
echo.
set /p COMMIT_MSG=💬 Digite a mensagem do commit: 

if "!COMMIT_MSG!"=="" (
    echo ⚠️ Commit cancelado: mensagem em branco.
    pause
    exit /b
)

REM ===============================
REM 4. ENVIAR ALTERAÇÕES
REM ===============================
git add .
git commit -m "!COMMIT_MSG!"
git push origin main

echo ✅ Alterações enviadas com sucesso!
pause
