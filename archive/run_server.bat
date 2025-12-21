@echo off
cd /d "%~dp0"
call venv\Scripts\activate
echo Starting Streamlit Server...
streamlit run main.py
pause
