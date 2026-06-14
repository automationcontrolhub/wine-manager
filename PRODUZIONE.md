# Guida al Deploy in Produzione

## Prerequisiti

- Server Linux (Ubuntu 22.04+ consigliato) con almeno 2 GB RAM
- Docker Engine ≥ 24.x
- Docker Compose plugin (`docker compose`)
- Accesso SSH al server
- Dominio DNS puntato sull'IP del server (opzionale ma consigliato per HTTPS)

---

## 1. Clonare il repository

```bash
git clone <URL_REPO> /opt/wine-manager
cd /opt/wine-manager
```

---

## 2. Creare il file `.env.prod`

```bash
cp env.prod.example .env.prod
nano .env.prod
```

### Variabili da configurare obbligatoriamente

| Variabile | Come ottenerla |
|---|---|
| `SECRET_KEY` | Esegui: `python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `POSTGRES_PASSWORD` | Scegli una password forte (min 20 caratteri) |
| `ALLOWED_HOSTS` | Il tuo dominio, es. `miosito.it,www.miosito.it` |
| `GMAIL_USER` | Indirizzo Gmail da cui inviare i backup |
| `GMAIL_PASSWORD` | **App Password a 16 caratteri** (vedi sotto) |
| `BACKUP_EMAIL` | Email dove ricevere i backup giornalieri |

### Come ottenere una Gmail App Password

1. Abilita la **verifica in due passaggi** su Google: [myaccount.google.com/security](https://myaccount.google.com/security)
2. Vai su [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Seleziona "Altra app (nome personalizzato)" → scrivi "Wine Manager"
4. Google genererà una password di **16 caratteri** (es. `abcd efgh ijkl mnop`)
5. Inseriscila in `GMAIL_PASSWORD` **senza spazi**: `abcdefghijklmnop`

> ⚠️ Non usare la password del tuo account Google. Solo le App Password funzionano con SMTP.

---

## 3. Aggiornare l'host in Nginx (opzionale)

Se hai un dominio, modifica `nginx/nginx.conf`:

```nginx
# Riga ~18 — sostituisci _ con il tuo dominio
server_name miosito.it www.miosito.it;
```

---

## 4. Abilitare HTTPS con Let's Encrypt (opzionale ma consigliato)

### Installare Certbot

```bash
sudo apt install certbot
sudo certbot certonly --standalone -d miosito.it -d www.miosito.it
```

I certificati vengono salvati in `/etc/letsencrypt/live/miosito.it/`.

### Aggiornare `nginx/nginx.conf`

Decommenta il blocco HTTPS alla fine del file e imposta:

```nginx
ssl_certificate     /etc/letsencrypt/live/miosito.it/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/miosito.it/privkey.pem;
```

### Montare i certificati in `docker-compose.prod.yml`

Nel servizio `nginx`, aggiungi sotto `volumes`:

```yaml
- /etc/letsencrypt:/etc/letsencrypt:ro
```

### Rinnovo automatico

```bash
sudo crontab -e
# Aggiungi:
0 3 1 * * certbot renew --quiet && docker compose -f /opt/wine-manager/docker-compose.prod.yml restart nginx
```

---

## 5. Primo avvio

```bash
cd /opt/wine-manager

# Build e avvio di tutti i servizi
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

Al primo avvio il backend:
1. Aspetta che il database sia pronto
2. Esegue `makemigrations` e `migrate`
3. Raccoglie i file statici
4. Crea l'utente admin con le credenziali di `.env.prod`
5. Avvia Daphne (ASGI)

### Verificare che tutto sia partito

```bash
docker compose -f docker-compose.prod.yml ps
```

Tutti i servizi devono essere `Up` o `healthy`.

### Controllare i log

```bash
# Tutti i servizi
docker compose -f docker-compose.prod.yml logs -f

# Solo il backend
docker compose -f docker-compose.prod.yml logs -f backend
```

---

## 6. Credenziali admin

Le credenziali del pannello `/admin/` sono quelle impostate in `.env.prod`:

```
DJANGO_SUPERUSER_USERNAME=...
DJANGO_SUPERUSER_PASSWORD=...
```

---

## 7. Comandi di gestione

```bash
# Riavviare un singolo servizio
docker compose -f docker-compose.prod.yml restart backend

# Fermare tutto
docker compose -f docker-compose.prod.yml down

# Fermare tutto e cancellare i volumi (⚠️ CANCELLA I DATI)
docker compose -f docker-compose.prod.yml down -v

# Aggiornare dopo un push
git pull
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build

# Eseguire un backup manuale
docker compose -f docker-compose.prod.yml exec backup python /app/backup.py

# Accedere alla shell Django
docker compose -f docker-compose.prod.yml exec backend python manage.py shell
```

---

## 8. Struttura dei servizi

```
[Internet]
    │
    ▼
[nginx :80/:443]  ← porta pubblica
    │
    ├─ /api/      → [backend :8000]  (Daphne/ASGI)
    ├─ /ws/       → [backend :8000]  (WebSocket)
    ├─ /admin/    → [backend :8000]
    ├─ /static/   → volume staticfiles
    └─ /          → [frontend :80]   (Nginx SPA)

[backend] ─── [db postgres:5432]
[backend] ─── [redis :6379]
[backup]  ─── [db postgres:5432]  (pg_dump ogni notte alle 02:00)
```

---

## 9. Backup

I backup vengono eseguiti automaticamente ogni notte alle **02:00** e:
- Salvati compressi (`.sql.gz`) nel volume `backup_data`
- Inviati via email a `BACKUP_EMAIL`
- I backup più vecchi di `BACKUP_KEEP_DAYS` giorni vengono eliminati automaticamente

### Ripristino da backup

```bash
# Copia il file di backup dal container
docker compose -f docker-compose.prod.yml cp backup:/backups/wine_backup_YYYYMMDD_HHMMSS.sql.gz .

# Decomprimi
gunzip wine_backup_YYYYMMDD_HHMMSS.sql.gz

# Ripristina
docker compose -f docker-compose.prod.yml exec -T db \
  psql -U $POSTGRES_USER -d $POSTGRES_DB < wine_backup_YYYYMMDD_HHMMSS.sql
```

---

## 10. Troubleshooting

### Il backend non si avvia

```bash
docker compose -f docker-compose.prod.yml logs backend
```

Cause comuni:
- `POSTGRES_PASSWORD` diversa tra `backend` e `db`
- `SECRET_KEY` non impostata in `.env.prod`
- `ALLOWED_HOSTS` non include il dominio

### La pagina mostra "502 Bad Gateway"

Il backend non è ancora pronto. Aspetta 30 secondi e riprova, oppure controlla:

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs backend --tail=30
```

### I file statici non si caricano

```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --clear --no-input
docker compose -f docker-compose.prod.yml restart nginx
```

docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build