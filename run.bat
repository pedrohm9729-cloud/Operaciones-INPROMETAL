@echo off
:: Navega automaticamente al directorio donde esta este archivo
cd /d "%~dp0"

echo ===================================================
echo   INICIANDO EXTRACTOR DE GASTOS BANCARIOS
echo ===================================================
echo.

:: Ejecucion usando el interprete de Python de Miniconda
set "PATH=C:\Users\Phenmor\miniconda3;C:\Users\Phenmor\miniconda3\Library\bin;C:\Users\Phenmor\miniconda3\Scripts;%PATH%"
C:\Users\Phenmor\miniconda3\python.exe gastos_bancarios.py --non-interactive

:: ===================================================
:: NOTA: Si usas un entorno virtual (.venv), descomenta 
:: las siguientes tres lineas (quitando los "::") y 
:: comenta la linea "python gastos_bancarios.py" de arriba:
:: ===================================================
:: call .venv\Scripts\activate
:: python gastos_bancarios.py --non-interactive
:: deactivate

echo.
echo ===================================================
echo   PROCESO TERMINADO - Cerrando en 5 segundos...
echo ===================================================
timeout /t 5
