#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
GOLD='\033[0;33m'
NC='\033[0m' # No Color

clear

echo ""
echo -e "${GOLD}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GOLD}║                                                               ║${NC}"
echo -e "${GOLD}║   🏷️  GUTTERIDGE PRICE TRACKER                                ║${NC}"
echo -e "${GOLD}║                                                               ║${NC}"
echo -e "${GOLD}║   Monitora i prezzi dei tuoi prodotti preferiti               ║${NC}"
echo -e "${GOLD}║                                                               ║${NC}"
echo -e "${GOLD}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Python non trovato! Installa Python 3.8+${NC}"
    exit 1
fi

# Use python3 if available, otherwise python
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

# Check if requirements are installed
echo -e "${BLUE}📦 Verifica dipendenze...${NC}"
if ! $PYTHON_CMD -c "import flask" &> /dev/null; then
    echo -e "${YELLOW}📥 Installazione dipendenze in corso...${NC}"
    pip3 install -r requirements.txt || pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Errore durante l'installazione delle dipendenze${NC}"
        exit 1
    fi
fi

# Initialize database if not exists
if [ ! -f "gutteridge_tracker.db" ]; then
    echo -e "${BLUE}🗄️ Inizializzazione database...${NC}"
    $PYTHON_CMD database.py
fi

echo ""
echo -e "${GREEN}✅ Tutto pronto!${NC}"
echo ""
echo -e "${GREEN}🚀 Avvio server su http://localhost:5000${NC}"
echo -e "${BLUE}🌐 Apri il browser manualmente se non si apre automaticamente${NC}"
echo ""
echo -e "${YELLOW}⏹️  Premi CTRL+C per fermare il server${NC}"
echo -e "${GOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Try to open browser (works on macOS and Linux with xdg-open)
if command -v xdg-open &> /dev/null; then
    xdg-open "http://localhost:5000" &> /dev/null &
elif command -v open &> /dev/null; then
    open "http://localhost:5000" &> /dev/null &
fi

# Start the Flask server
$PYTHON_CMD app.py
