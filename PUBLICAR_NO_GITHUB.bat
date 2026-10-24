@echo off
chcp 65001 >nul
title Publicar Dashboard no GitHub e Streamlit Cloud - PROFAGUA UNEMAT
echo =====================================================================
echo  PRODUTO TECNOLOGICO PROFAGUA / UNEMAT
echo  Assistente de Publicacao na Nuvem (GitHub & Streamlit Cloud)
echo =====================================================================
echo.
cd /d "%~dp0"

REM Garantir que git e gh estao no PATH desta sessao
set "PATH=C:\Program Files\Git\bin;C:\Program Files\Git\cmd;C:\Program Files\GitHub CLI;%PATH%"

echo [1/3] Verificando conexao com sua conta do GitHub...
gh auth status >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo =====================================================================
    echo  ATENCAO: Voce precisa autorizar o acesso ao seu GitHub.
    echo  O navegador vai abrir uma pagina do GitHub.
    echo  Basta clicar em "Authorize github" para conectar.
    echo =====================================================================
    echo.
    gh auth login --web -p https -w
)

echo.
echo [2/3] Criando o repositorio no GitHub e enviando os arquivos...
gh repo create barragens-mt-profagua --public --source=. --remote=origin --push
if %errorlevel% neq 0 (
    echo.
    echo Repositorio ja existe ou atualizando... Enviando alteracoes:
    git push -u origin main
)

echo.
echo =====================================================================
echo  [3/3] Arquivos enviados com sucesso para o GitHub!
echo.
echo  Abrindo o Streamlit Community Cloud no seu navegador...
echo  Para finalizar a publicacao:
echo    1. No site que vai abrir, clique em "New App" (ou "Create app")
echo    2. Em "Repository", selecione: barragens-mt-profagua
echo    3. Em "Main file path", confirme: app_dashboard_barragens.py
echo    4. Clique no botao "Deploy!"
echo =====================================================================
start https://share.streamlit.io
echo.
rem pause
