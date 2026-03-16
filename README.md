# 🏷️ Gutteridge Price Tracker

Un'applicazione elegante per tracciare i prezzi dei prodotti su [Gutteridge.com](https://www.gutteridge.com/it_IT/) e visualizzare l'andamento nel tempo.

## ✨ Funzionalità

### Core
- **Tracciamento prezzi**: Aggiungi prodotti tramite URL e monitora le variazioni di prezzo
- **Grafico storico**: Visualizza l'andamento del prezzo nel tempo con Chart.js
- **Immagini originali**: Mostra le immagini originali dei prodotti con galleria
- **Aggiornamento automatico**: I prezzi vengono aggiornati ogni 6 ore

### Avanzate
- **🌓 Dark Mode**: Tema scuro/chiario con preferenza salvata
- **🔍 Ricerca**: Cerca tra i prodotti tracciati
- **📊 Ordinamento**: Ordina per data, prezzo o nome
- **📥 Export**: Esporta dati in CSV o JSON
- **🔔 Alert Prezzo**: Ricevi notifiche quando il prezzo scende
- **📈 Statistiche**: Prezzo minimo, massimo e medio

## 📁 Struttura del Progetto

```
gutteridge-price-tracker/
├── 📄 app.py                 # Server Flask principale
├── 📄 database.py            # Gestione database SQLite
├── 📄 scraper.py             # Web scraper per Gutteridge
├── 📄 config.py              # Configurazione centralizzata
├── 📄 requirements.txt       # Dipendenze Python
├── 📄 README.md              # Documentazione
├── 📄 .gitignore             # File da ignorare in Git
│
├── 🚀 start.bat              # Launcher Windows
├── 🚀 start.sh               # Launcher Linux/Mac
│
├── 📂 templates/
│   └── 📄 index.html         # Pagina principale
│
├── 📂 static/
│   ├── 📄 style.css          # Stili CSS premium
│   ├── 📄 app.js             # Logica frontend
│   └── 📄 placeholder.svg    # Immagine placeholder
│
├── 📂 data/                  # Database SQLite
│   └── 📄 gutteridge_tracker.db
│
├── 📂 logs/                  # File di log
│   └── 📄 app.log
│
└── 📂 src/                   # Package Python
    ├── 📄 __init__.py
    ├── 📂 api/
    ├── 📂 scraper/
    ├── 📂 database/
    └── 📂 utils/
```

## 🚀 Installazione

### Prerequisiti
- Python 3.8+
- pip

### Setup Rapido

1. **Clona il progetto**:
```bash
git clone <repository-url>
cd gutteridge-price-tracker
```

2. **Avvia con il launcher**:

**Windows**:
```bash
start.bat
```

**Linux/Mac**:
```bash
chmod +x start.sh
./start.sh
```

### Setup Manuale

1. **Installa dipendenze**:
```bash
pip install -r requirements.txt
```

2. **Inizializza database**:
```bash
python database.py
```

3. **Avvia server**:
```bash
python app.py
```

4. **Apri browser**:
```
http://localhost:5000
```

## 📖 Utilizzo

### Aggiungere un Prodotto

1. Vai su [Gutteridge.com](https://www.gutteridge.com/it_IT/)
2. Trova il prodotto che vuoi tracciare
3. Copia l'URL dalla barra degli indirizzi
4. Incolla l'URL nel campo di input
5. Clicca su "Aggiungi"

### Visualizzare lo Storico

1. Clicca su un prodotto nella griglia
2. Visualizza il grafico dell'andamento prezzi
3. Consulta le statistiche (min, max, media)

### Impostare un Alert

1. Apri il dettaglio di un prodotto
2. Clicca su "🔔 Alert"
3. Inserisci il prezzo target
4. Clicca "Crea Alert"

### Esportare Dati

- **CSV singolo**: Clicca "📥 CSV" nel modal prodotto
- **JSON singolo**: Clicca "📋 JSON" nel modal prodotto
- **CSV tutti**: Clicca "📥 CSV" nella sezione prodotti

## 🔧 API Endpoints

| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| `GET` | `/api/products` | Lista tutti i prodotti |
| `POST` | `/api/products` | Aggiungi un nuovo prodotto |
| `GET` | `/api/products/:id` | Dettagli di un prodotto |
| `DELETE` | `/api/products/:id` | Elimina un prodotto |
| `GET` | `/api/products/:id/history` | Storico prezzi |
| `POST` | `/api/products/:id/refresh` | Aggiorna prezzo |
| `POST` | `/api/products/refresh-all` | Aggiorna tutti i prezzi |
| `GET` | `/api/products/:id/images` | Tutte le immagini |
| `GET` | `/api/products/search?q=` | Cerca prodotti |
| `GET` | `/api/products/sort?by=&order=` | Ordina prodotti |
| `GET` | `/api/products/:id/export/csv` | Export CSV |
| `GET` | `/api/products/:id/export/json` | Export JSON |
| `GET` | `/api/products/export/all/csv` | Export tutti CSV |
| `GET` | `/api/alerts` | Lista alert |
| `POST` | `/api/alerts` | Crea alert |
| `DELETE` | `/api/alerts/:id` | Elimina alert |
| `POST` | `/api/alerts/check` | Controlla alert |
| `GET` | `/api/stats` | Statistiche generali |

## ⚙️ Configurazione

Modifica [`config.py`](config.py) per personalizzare:

```python
# Porta del server
PORT = 5000

# Intervallo aggiornamento prezzi (ore)
PRICE_UPDATE_INTERVAL_HOURS = 6

# Timeout richieste (secondi)
REQUEST_TIMEOUT = 30
```

## 🛠️ Tecnologie

| Componente | Tecnologia |
|------------|------------|
| **Backend** | Python, Flask |
| **Database** | SQLite |
| **Web Scraping** | BeautifulSoup, Requests |
| **Frontend** | HTML5, CSS3, JavaScript |
| **Grafici** | Chart.js |
| **Scheduling** | Schedule |
| **Font** | Inter (Google Fonts) |

## 🎨 Design System

### Colori
- **Primario**: `#c9a962` (Oro)
- **Background**: `#f8f9fa` (Chiaro) / `#0d1117` (Scuro)
- **Testo**: `#1a1a2e` (Chiaro) / `#f0f6fc` (Scuro)

### Componenti
- Border radius: 8px, 12px, 16px, 24px
- Shadows: xs, sm, md, lg, xl
- Transizioni: 150ms, 250ms, 400ms

## 📝 Note

- Lo scraper è progettato per la struttura attuale del sito Gutteridge
- Rispetta i termini di servizio del sito web
- L'applicazione è pensata per uso personale
- Il codice è facilmente aggiornabile tramite [`config.py`](config.py)

## 📄 Licenza

Questo progetto è per uso personale e didattico.
