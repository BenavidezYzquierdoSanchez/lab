@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo [FraudCloud] Verificando dependencias...
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo ERROR: Compruebe la instalacion de Python o su conexion a Internet.
  pause
  exit /b 1
)
echo [FraudCloud] Iniciando dashboard en http://localhost:8501 ...
python -m streamlit run streamlit_app.py
pause
