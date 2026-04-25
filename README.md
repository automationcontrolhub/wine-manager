# 🍷 VinoManager — Gestionale Vinicolo

Sistema gestionale per strutture vinicole con gestione completa di:
- **Tipologie di vino** con silos e materiali associati
- **Magazzino** materiali (tappi, cartoni, bottiglie, etichette, capsule, cestelli)
- **Imbottigliamento** con flusso a 2 step (con/senza etichetta)
- **Tracciabilità** movimenti di magazzino

## Stack Tecnologico

- **Backend**: Django 5 + Django REST Framework
- **Frontend**: React 18 + Vite + TailwindCSS
- **Database**: PostgreSQL 16
- **Containerizzazione**: Docker Compose

## Quick Start

```bash
# 1. Clona e avvia
docker compose up --build

# 2. Accedi
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000/api/
# Admin Django: http://localhost:8000/admin/ (admin/admin)
```

## Flusso di utilizzo

### 1. Configurazione iniziale
Vai su **Configurazione** e crea le tipologie di materiali:
- Cartoni (con capacità bottiglie)
- Tappi (es: Diam5, Diam10, Spumante)
- Bottiglie (con capacità in litri)
- Etichette
- Capsule
- Cestelli (per spumanti)

### 2. Crea famiglie e tipologie di vino
Vai su **Tipologie Vino**:
- Crea le famiglie (es: Etna DOC, Contrade, Spumante)
- Per ogni famiglia, crea le tipologie associando i materiali specifici

### 3. Carica magazzino
Vai su **Magazzino**:
- Carica le scorte di materiali
- Aggiungi vino ai silos

### 4. Imbottigliamento
Vai su **Imbottigliamento**:
- **Crea senza etichetta**: crea bottiglie senza etichetta (stadio intermedio)
- **Crea con etichetta**: crea bottiglie complete direttamente
- **Associa etichetta**: completa bottiglie create senza etichetta

## Logica dei lotti

Le bottiglie non sono tracciate singolarmente ma per **lotti** aggregati.
Ogni lotto ha: tipologia vino, quantità, stato (senza_etichetta/completa), flag capsula.

Quando si associa un'etichetta:
1. Si scala la quantità dal lotto "senza etichetta"
2. Si crea/incrementa il lotto "completa" con le stesse caratteristiche
3. Si scalano etichette (e capsule se necessario) dal magazzino

## API Endpoints principali

| Endpoint | Metodo | Descrizione |
|---|---|---|
| `/api/dashboard/` | GET | Riepilogo generale |
| `/api/tipologie-vino/` | CRUD | Gestione tipologie |
| `/api/famiglie/` | CRUD | Gestione famiglie |
| `/api/carico-magazzino/` | POST | Carico materiali |
| `/api/aggiunta-vino/` | POST | Aggiunta vino al silos |
| `/api/crea-senza-etichetta/` | POST | Imbottigliamento senza etichetta |
| `/api/crea-con-etichetta/` | POST | Imbottigliamento con etichetta |
| `/api/associa-etichetta/` | POST | Associazione etichetta |
| `/api/bottiglie-senza-etichetta/` | GET | Riepilogo bottiglie in attesa |
