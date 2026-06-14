@echo off
cd /d "%~dp0"
echo ===================================================
echo   INICIANDO AUTENTICACION DE GMAIL (GOOGLE)
echo ===================================================
echo.
set "PATH=C:\Users\Phenmor\miniconda3;C:\Users\Phenmor\miniconda3\Library\bin;C:\Users\Phenmor\miniconda3\Scripts;%PATH%"
C:\Users\Phenmor\miniconda3\python.exe gastos_bancarios.py
echo.
echo ===================================================
echo   PROCESO TERMINADO
echo ===================================================
pause
