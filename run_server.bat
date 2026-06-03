@echo off
:: Navega automaticamente al directorio donde esta este archivo
cd /d "%~dp0"

echo ===================================================
echo   INICIANDO SERVIDOR DEL DASHBOARD DE GASTOS BANCARIOS
echo ===================================================
echo.

:: Ejecucion usando el interprete de Python de Miniconda
set "PATH=C:\Users\Phenmor\miniconda3;C:\Users\Phenmor\miniconda3\Library\bin;C:\Users\Phenmor\miniconda3\Scripts;%PATH%"
C:\Users\Phenmor\miniconda3\python.exe server.py

echo.
echo ===================================================
echo   SERVIDOR DETENIDO o ERROR AL INICIAR
echo ===================================================
pause
