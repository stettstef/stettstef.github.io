@echo off
cd C:\Users\stefa\OneDrive\Documentos\GitHub\stettstef.github.io

start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" http://localhost:8501

streamlit run second_brain_app.py --server.headless true