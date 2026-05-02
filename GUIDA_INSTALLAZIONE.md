# 🍷 VinoManager — Guida Completa all'Installazione e Utilizzo

## 📋 Indice
1. [Requisiti di Sistema](#requisiti-di-sistema)
2. [Installazione Docker](#installazione-docker)
3. [Installazione VinoManager](#installazione-vinomanager)
4. [Primo Avvio](#primo-avvio)
5. [Guida all'Uso](#guida-alluso)
6. [Risoluzione Problemi](#risoluzione-problemi)
7. [Backup e Manutenzione](#backup-e-manutenzione)

---

## 📦 Requisiti di Sistema

### Sistema Operativo
- **Windows 10/11** (64-bit)
- **macOS** 10.15 o superiore
- **Linux** (Ubuntu 20.04+, Debian, Fedora, ecc.)

### Hardware Minimo
- **RAM**: 4GB (8GB raccomandati)
- **Spazio disco**: 2GB liberi
- **Processore**: Qualsiasi CPU moderna (2+ core)

---

## 🐳 Installazione Docker

Docker è necessario per far funzionare VinoManager. Segui la guida per il tuo sistema operativo:

### Windows

1. **Scarica Docker Desktop**
   - Vai su: https://www.docker.com/products/docker-desktop/
   - Clicca su "Download for Windows"
   - Scarica il file `.exe`

2. **Installa Docker Desktop**
   - Esegui il file scaricato
   - Segui la procedura guidata (clicca "Next" → "Next" → "Install")
   - Al termine, riavvia il computer se richiesto

3. **Avvia Docker Desktop**
   - Cerca "Docker Desktop" nel menu Start
   - Avvia l'applicazione
   - Attendi che appaia "Docker Desktop is running" nell'icona della barra applicazioni

4. **Verifica l'installazione**
   - Apri il Prompt dei comandi (cerca "cmd" nel menu Start)
   - Digita: `docker --version`
   - Dovresti vedere qualcosa come: `Docker version 24.0.x`

### macOS

1. **Scarica Docker Desktop**
   - Vai su: https://www.docker.com/products/docker-desktop/
   - Scegli il download per il tuo chip:
     - **Apple Silicon (M1/M2/M3)**: "Download for Mac - Apple Chip"
     - **Intel**: "Download for Mac - Intel Chip"

2. **Installa Docker Desktop**
   - Apri il file `.dmg` scaricato
   - Trascina l'icona Docker nelle Applicazioni
   - Apri Docker dalle Applicazioni

3. **Avvia Docker Desktop**
   - Alla prima apertura, accetta i permessi richiesti
   - Attendi che Docker si avvii completamente (icona nella barra superiore)

4. **Verifica l'installazione**
   - Apri Terminale (Applicazioni → Utility → Terminale)
   - Digita: `docker --version`
   - Dovresti vedere: `Docker version 24.0.x`

### Linux (Ubuntu/Debian)

1. **Apri il Terminale** (Ctrl+Alt+T)

2. **Installa Docker** (copia e incolla questi comandi uno alla volta):

```bash
# Aggiorna i pacchetti
sudo apt-get update

# Installa dipendenze
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# Aggiungi la chiave GPG ufficiale di Docker
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Aggiungi il repository Docker
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Installa Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Avvia Docker
sudo systemctl start docker
sudo systemctl enable docker

# Permetti al tuo utente di usare Docker senza sudo
sudo usermod -aG docker $USER
```

3. **Riavvia il computer** (necessario per applicare i permessi)

4. **Verifica l'installazione**:
```bash
docker --version
```

---

## 🚀 Installazione VinoManager

### 1. Estrai il file ZIP

**Windows:**
- Tasto destro sul file `wine-manager.tar.gz`
- Seleziona "Estrai tutto..." o usa 7-Zip/WinRAR
- Se hai solo `.tar.gz`, potrebbe essere necessario estrarre due volte (prima `.gz`, poi `.tar`)
- Salva la cartella estratta in un posto facile da trovare (es: `C:\VinoManager`)

**macOS:**
- Doppio click sul file `wine-manager.tar.gz`
- Si estrarrà automaticamente
- Sposta la cartella `wine-manager` sul Desktop o dove preferisci

**Linux:**
```bash
# Naviga dove hai scaricato il file
cd ~/Download

# Estrai
tar -xzf wine-manager.tar.gz

# Sposta nella home (opzionale)
mv wine-manager ~/wine-manager
```

### 2. Apri il Terminale/Prompt nella cartella

**Windows:**
- Apri la cartella `wine-manager` estratta
- Nella barra degli indirizzi in alto, scrivi `cmd` e premi Invio
- Si aprirà il Prompt dei comandi nella cartella corretta

**macOS:**
- Apri Terminale
- Digita `cd ` (con lo spazio finale)
- Trascina la cartella `wine-manager` nella finestra del Terminale
- Premi Invio

**Linux:**
```bash
cd ~/wine-manager  # o il percorso dove hai estratto
```

### 3. Avvia VinoManager

Nel terminale/prompt aperto, digita:

```bash
docker compose up --build
```

**Cosa succede:**
- La prima volta scaricherà tutte le componenti necessarie (può richiedere 5-10 minuti)
- Vedrai scorrere molti log — è normale
- Quando vedi messaggi come `backend-1 | ... "GET /api/..." HTTP/1.1" 200`, è pronto

**NON chiudere la finestra del terminale** — il sistema è in esecuzione qui.

---

## 🎯 Primo Avvio

### 1. Accedi all'applicazione

Apri il browser (Chrome, Firefox, Safari, Edge) e vai a:

```
http://localhost:5173
```

Vedrai la **Dashboard** di VinoManager.

### 2. Credenziali Amministratore

Per accedere al pannello di amministrazione Django (opzionale, per utenti avanzati):

- URL: `http://localhost:8000/admin/`
- **Username**: `admin`
- **Password**: `admin`

⚠️ **IMPORTANTE**: Cambia questa password in produzione!

---

## 📚 Guida all'Uso

### Flusso di Lavoro Consigliato

#### STEP 1: Configurazione Materiali

Prima di tutto, vai su **Configurazione** e crea le tipologie di materiali:

1. **Cartoni**
   - Nome: es. "Normale 6 bott. 0.75"
   - Capacità: 6 (quante bottiglie contiene)
   
2. **Tappi**
   - Nome: es. "Diam5", "Diam10", "Spumante"
   
3. **Bottiglie**
   - Nome: es. "Tipo 1 0.75L"
   - Capacità: 0.75 (litri)
   
4. **Etichette**
   - Nome: es. "Tipo 1 0.75L", "Tipo Spumante"
   
5. **Capsule**
   - Nome: es. "Tipo 1", "Spumante"
   
6. **Cestelli** (solo per spumanti)
   - Nome: es. "Spumante"

#### STEP 2: Crea Famiglie e Tipologie di Vino

Vai su **Tipologie Vino**:

1. **Crea una Famiglia** (es: "Etna DOC", "Spumante")
   - Spunta "È uno spumante" se necessario
   
2. **Crea le Tipologie** per ogni famiglia:
   - Nome: es. "Rosso", "Bianco", "SN35 Brut Nature"
   - Famiglia: scegli la famiglia creata
   - Quantità iniziale nel silos: es. 5000 litri
   - Associa i materiali specifici per questa tipologia

**Importante**: Ogni tipologia ha i suoi materiali associati (tappo, bottiglia, etichetta, capsula, cartone, cestello). Il sistema li userà automaticamente durante l'imbottigliamento.

#### STEP 3: Carica il Magazzino

Vai su **Magazzino**:

1. **Carico Materiali**
   - Clicca "Carico Materiale"
   - Seleziona categoria (es: Tappi)
   - Seleziona tipo (es: Diam5)
   - Inserisci quantità (es: 10000)
   - Ripeti per ogni materiale

2. **Aggiungi Vino**
   - Clicca "Aggiungi Vino"
   - Seleziona tipologia
   - Inserisci litri da aggiungere al silos

#### STEP 4: Imbottigliamento

Vai su **Imbottigliamento**. Hai 3 opzioni:

**A) Crea SENZA etichetta** (per etichettare in seguito)
- Seleziona tipologia vino
- Inserisci quantità bottiglie
- Scegli se applicare capsula ora
- Il sistema scala: vino, bottiglie, tappi, (capsule), cartoni, (cestelli)
- Le bottiglie vanno in "Attesa etichetta"

**B) Crea CON etichetta** (bottiglia completa)
- Seleziona tipologia vino
- Inserisci quantità bottiglie
- Scegli se applicare capsula (di default sì)
- Il sistema scala: vino, bottiglie, tappi, etichette, (capsule), cartoni, (cestelli)
- Le bottiglie sono complete e pronte

**C) Associa etichetta** (completa bottiglie senza etichetta)
- **Tipologia origine**: da dove prendere le bottiglie senza etichetta
- **Tipologia destinazione**: quale etichetta applicare (può essere diversa!)
- Quantità da etichettare
- Flag capsula: se attivo, prende PRIMA bottiglie senza capsula

**Esempio pratico:**
- Hai 500 bottiglie "Etna DOC Rosso" senza etichetta
- Puoi etichettarle come "Etna DOC Bianco" (riutilizzo!)
- Sistema scala solo l'etichetta dal magazzino

#### Riepilogo Materiali

Durante la creazione, il sistema mostra in anteprima:
- Litri di vino necessari
- Quante bottiglie, tappi, etichette, capsule servono
- Quanti cartoni servono (calcolati automaticamente)
- Cestelli (solo per spumanti)

Se manca qualcosa, ricevi un errore chiaro prima di procedere.

---

## 🔧 Risoluzione Problemi

### Docker Desktop non si avvia

**Windows:**
- Verifica che la virtualizzazione sia abilitata nel BIOS
- Vai su: Pannello di controllo → Programmi → Attiva o disattiva funzionalità Windows
- Abilita "Hyper-V" e "Contenitori Windows"

**macOS:**
- Assicurati di avere almeno macOS 10.15
- Controlla che Docker Desktop abbia i permessi necessari in Preferenze di Sistema → Sicurezza

### L'applicazione non si apre su localhost:5173

1. Verifica che Docker sia in esecuzione
2. Nel terminale dove hai lanciato `docker compose up`, controlla che non ci siano errori
3. Aspetta qualche minuto — la prima volta può richiedere tempo
4. Prova a fermare tutto (Ctrl+C nel terminale) e rilancia:
   ```bash
   docker compose down
   docker compose up --build
   ```

### Errori "relation does not exist"

Il database non è stato creato. Ferma tutto e riavvia pulendo i volumi:
```bash
docker compose down -v
docker compose up --build
```

### Porto già in uso (port already allocated)

Un altro programma usa le porte 5173 o 8000. Due opzioni:

**Opzione 1** — Trova e chiudi il programma che usa quella porta

**Opzione 2** — Cambia le porte nel file `docker-compose.yml`:
```yaml
# Cerca queste righe e cambia i numeri prima dei :
ports:
  - "5174:5173"  # Era 5173:5173, ora usa 5174
  - "8001:8000"  # Era 8000:8000, ora usa 8001
```
Poi accedi a `http://localhost:5174`

### Password dimenticata

L'utente admin si ricrea ogni volta. Password di default: `admin`

---

## 💾 Backup e Manutenzione

### Come fare un backup del database

1. **Esporta i dati**:
```bash
docker compose exec backend python manage.py dumpdata > backup.json
```

2. **Salva il file** `backup.json` in un posto sicuro

### Come ripristinare un backup

1. **Copia il file backup.json** nella cartella `wine-manager/backend/`

2. **Esegui**:
```bash
docker compose exec backend python manage.py loaddata backup.json
```

### Come fermare VinoManager

Nel terminale dove è in esecuzione, premi **Ctrl+C**

### Come riavviare VinoManager

Nella cartella `wine-manager`, esegui:
```bash
docker compose up
```
(senza `--build`, più veloce)

### Come aggiornare VinoManager

Quando ricevi una nuova versione:
1. Fai un backup (vedi sopra)
2. Ferma l'applicazione (Ctrl+C)
3. Sostituisci i file con la nuova versione
4. Lancia `docker compose up --build`

### Pulizia completa (reset totale)

⚠️ **ATTENZIONE**: Questo cancella TUTTI i dati!

```bash
docker compose down -v
docker compose up --build
```

---

## 📞 Supporto

### Log e Debug

Per vedere i log dettagliati:
```bash
docker compose logs backend
docker compose logs frontend
docker compose logs db
```

### Informazioni di Sistema

- **Backend API**: http://localhost:8000/api/
- **Admin Django**: http://localhost:8000/admin/
- **Frontend**: http://localhost:5173
- **Database**: PostgreSQL su porta 5432

### Comandi Utili

```bash
# Vedere tutti i container in esecuzione
docker ps

# Fermare tutto
docker compose down

# Fermare tutto e cancellare volumi (reset)
docker compose down -v

# Riavviare un singolo servizio
docker compose restart backend

# Vedere l'uso di risorse
docker stats
```

---

## 🎓 Consigli d'Uso

### Best Practices

1. **Fai backup regolari** (almeno settimanali)
2. **Controlla sempre l'anteprima materiali** prima di confermare un imbottigliamento
3. **Usa nomi chiari** per le tipologie (es: "Etna DOC Rosso 2023")
4. **Carica il magazzino prima** di iniziare a imbottigliare
5. **Tieni Docker Desktop sempre aggiornato**

### Workflow Consigliato

```
Configurazione → Tipologie → Magazzino → Imbottigliamento → Dashboard
```

### Sicurezza

- Non esporre pubblicamente su Internet senza protezione
- Cambia la password admin in `docker-compose.yml` prima di usare in produzione
- Fai backup prima di operazioni massive

---

## ✅ Checklist Primo Utilizzo

- [ ] Docker installato e funzionante
- [ ] File estratto in una cartella permanente
- [ ] `docker compose up --build` eseguito con successo
- [ ] Browser aperto su http://localhost:5173
- [ ] Tipologie di materiali create in Configurazione
- [ ] Famiglie e tipologie vino create
- [ ] Magazzino caricato con materiali
- [ ] Primo imbottigliamento di test eseguito
- [ ] Backup del database fatto

---

**Versione**: 1.0  
**Ultimo aggiornamento**: Aprile 2026  

Buon lavoro con VinoManager! 🍷
