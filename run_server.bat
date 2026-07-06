@echo off
:: Navega automaticamente al directorio donde esta este archivo
cd /d "%~dp0"

echo ===================================================
echo   INICIANDO SERVIDOR DEL DASHBOARD DE GASTOS BANCARIOS
echo ===================================================
echo.

:: Ejecucion usando el interprete de Python del sistema
python server.py

echo.
echo ===================================================
echo   SERVIDOR DETENIDO o ERROR AL INICIAR
echo ===================================================
pause
