@echo off
title Ferretest - Sistema de Ferreteria
echo ===================================================
echo    Iniciando Servidor Ferretest (Streamlit)
echo ===================================================
echo.

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] No se encontro el entorno virtual en .venv.
    echo Asegurate de crearlo e instalar los requisitos primero.
    pause
    exit /b 1
)

echo Abriendo navegador en http://localhost:8501...
start "" http://localhost:8501

echo.
echo Presiona Ctrl+C o cierra esta ventana para detener el servidor.
echo.
.venv\Scripts\python.exe -m streamlit run app.py --server.headless false

pause
