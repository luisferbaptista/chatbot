@echo off
echo ================================
echo  Sistema de Gestion del Chatbot
echo ================================
echo.
echo Iniciando aplicacion de gestion...
echo.

REM Activar entorno virtual si existe
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Verificar si Streamlit está instalado
python -c "import streamlit" 2>nul
if errorlevel 1 (
    echo Streamlit no esta instalado. Instalando...
    pip install streamlit>=1.28.0
    echo.
)

REM Iniciar la aplicacion
echo Abriendo aplicacion en el navegador...
streamlit run bot_training_app.py

pause

