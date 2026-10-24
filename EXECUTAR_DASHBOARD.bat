@echo off
title Dashboard de Barragens SIMCAR-MT - PROFAGUA UNEMAT
echo =====================================================================
echo  PRODUTO TECNOLOGICO PROFAGUA / UNEMAT
echo  Iniciando Dashboard Interativo de Barragens (SIMCAR - MT)
echo =====================================================================
cd /d "%~dp0"
python -m streamlit run app_dashboard_barragens.py
pause
