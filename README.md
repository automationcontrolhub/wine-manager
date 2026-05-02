# 🍷 VinoManager — Gestionale Vinicolo

Sistema gestionale completo per strutture vinicole con gestione di:
- **Tipologie di vino** con silos e materiali associati
- **Magazzino** materiali (tappi, cartoni, bottiglie, etichette, capsule, cestelli)
- **Imbottigliamento** con flusso a 2 step (con/senza etichetta) e associazione flessibile
- **Tracciabilità** completa dei movimenti di magazzino
- **Sistema lotti aggregati** per gestire ~100.000 bottiglie/anno

## 📖 Documentazione

- **[GUIDA_INSTALLAZIONE.md](GUIDA_INSTALLAZIONE.md)** — Guida completa per principianti (include installazione Docker)
- **[QUICK_START.md](QUICK_START.md)** — Avvio rapido per utenti esperti

## Stack Tecnologico

- **Backend**: Django 5 + Django REST Framework + PostgreSQL 16
- **Frontend**: React 18 + Vite + TailwindCSS
- **Containerizzazione**: Docker Compose

## Quick Start

```bash
# 1. Estrai e naviga
tar -xzf wine-manager.tar.gz
cd wine-manager

# 2. Avvia (richiede Docker)
docker compose up --build

# 3. Apri browser
http://localhost:5173
```

**Prima volta?** Leggi [GUIDA_INSTALLAZIONE.md](GUIDA_INSTALLAZIONE.md) per installare Docker e configurare tutto.

## Caratteristiche Principali

### Configurazione Flessibile
Tutti i materiali (cartoni, tappi, bottiglie, etichette, capsule, cestelli) sono completamente configurabili dall'utente — niente valori preimpostati.

### Imbottigliamento Intelligente
- **Crea senza etichetta**: bottiglia in stadio intermedio, etichetta applicata dopo
- **Crea con etichetta**: bottiglia completa in un solo step
- **Associa etichetta**: completa bottiglie esistenti con **cross-type** (es: bottiglia vino X → etichetta vino Y)

### Gestione Capsule Ottimizzata
Flag capsula intelligente: quando attivo, prende prioritariamente bottiglie **senza** capsula per applicarle dove servono davvero.

### Sistema Lotti Aggregati
Le bottiglie non sono tracciate singolarmente ma in **lotti** aggregati per tipologia + stato + flag capsula. Questo permette di gestire decine di migliaia di bottiglie senza appesantire il database.

## Flusso di Utilizzo

### 1. Configurazione iniziale
Vai su **Configurazione** e crea le tipologie di materiali necessarie.

### 2. Crea famiglie e tipologie di vino
Vai su **Tipologie Vino**:
- Crea famiglie (es: Etna DOC, Contrade, Spumante)
- Per ogni famiglia, crea tipologie associando i materiali specifici

### 3. Carica magazzino
Vai su **Magazzino**:
- Carica scorte di materiali
- Aggiungi vino ai silos

### 4. Imbottigliamento
Vai su **Imbottigliamento** e scegli la modalità più adatta.

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
| `/api/associa-etichetta/` | POST | Associazione etichetta (anche cross-type) |
| `/api/bottiglie-senza-etichetta/` | GET | Riepilogo bottiglie in attesa |

## Accessi

- **Frontend**: http://localhost:5173
- **Admin Django**: http://localhost:8000/admin/ (user: `admin`, pass: `admin`)
- **API**: http://localhost:8000/api/

⚠️ **Cambia la password admin prima di usare in produzione!**

## Comandi Utili

```bash
# Stop
docker compose down

# Reset completo (cancella tutti i dati)
docker compose down -v
docker compose up --build

# Backup database
docker compose exec backend python manage.py dumpdata > backup.json

# Restore database
docker compose exec backend python manage.py loaddata backup.json

# Logs
docker compose logs -f backend
```

## Supporto

Per problemi comuni e risoluzione errori, consulta la sezione "Risoluzione Problemi" in [GUIDA_INSTALLAZIONE.md](GUIDA_INSTALLAZIONE.md).

## Licenza

Proprietario. Tutti i diritti riservati.

---

**Versione**: 1.0  
**Data**: Aprile 2026
