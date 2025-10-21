@echo off
REM Script para reiniciar el bot de Telegram de forma segura

echo ================================================
echo   REINICIANDO BOT DE TELEGRAM
echo ================================================
echo.

echo [1/3] Deteniendo procesos Python existentes...
taskkill /F /IM python.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo       ✓ Procesos detenidos correctamente
) else (
    echo       ! No habia procesos Python corriendo
)
echo.

echo [2/3] Esperando 2 segundos...
timeout /t 2 /nobreak >nul
echo       ✓ Listo
echo.

echo [3/3] Iniciando bot...
start /B C:\Users\l.baptista\AppData\Local\Programs\Python\Python311\python.exe bot.py
timeout /t 2 /nobreak >nul
echo       ✓ Bot iniciado en segundo plano
echo.

echo ================================================
echo   BOT REINICIADO EXITOSAMENTE
echo ================================================
echo.
echo El bot esta corriendo en segundo plano.
echo Presiona cualquier tecla para cerrar esta ventana...
pause >nul

