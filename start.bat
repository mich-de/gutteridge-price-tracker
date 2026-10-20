@echo off
chcp 65001 >nul
title Gutteridge Price Tracker

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║                                                               ║
echo ║   🏷️  GUTTERIDGE PRICE TRACKER                                ║
echo ║                                                               ║
echo ║   Monitora i prezzi dei tuoi prodotti preferiti               ║
echo ║                                                               ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python non trovato! Installa Python 3.8+ da https://python.org
    pause
    exit /b 1
)

:: Check if requirements are installed
echo 📦 Verifica dipendenze...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo 📥 Installazione dipendenze in corso...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Errore durante l'installazione delle dipendenze
        pause
        exit /b 1
    )
)

:: Initialize database if not exists
if not exist "gutteridge_tracker.db" (
    echo 🗄️ Inizializzazione database...
    python database.py
)

echo.
echo ✅ Tutto pronto!
echo.
echo 🚀 Avvio server su http://localhost:5000
echo 🌐 Il browser si aprirà automaticamente...
echo.
echo ⏹️  Premi CTRL+C per fermare il server
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

:: Open browser after a short delay
start "" "http://localhost:5000"

:: Start the Flask server
python app.py

pause
