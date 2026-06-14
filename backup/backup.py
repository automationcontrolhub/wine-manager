#!/usr/bin/env python3
"""
backup.py — Dump PostgreSQL + invio via Gmail SMTP.

Variabili d'ambiente richieste:
  DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
  GMAIL_USER     → indirizzo mittente Gmail (es: pippo@gmail.com)
  GMAIL_PASSWORD → App Password Gmail (non la password normale)
  BACKUP_EMAIL   → destinatario (es: tuo@gmail.com)
  BACKUP_KEEP_DAYS → quanti giorni conservare i backup locali (default 7)
"""
import os
import sys
import gzip
import shutil
import smtplib
import logging
import subprocess
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
log = logging.getLogger('backup')

# ── Configurazione ────────────────────────────────────────────────────────

BACKUP_DIR = Path(os.environ.get('BACKUP_DIR', '/backups'))
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

DB_HOST     = os.environ.get('DB_HOST', 'db')
DB_PORT     = os.environ.get('DB_PORT', '5432')
DB_NAME     = os.environ['DB_NAME']
DB_USER     = os.environ['DB_USER']
DB_PASSWORD = os.environ['DB_PASSWORD']

GMAIL_USER     = os.environ['GMAIL_USER']
GMAIL_PASSWORD = os.environ['GMAIL_PASSWORD']   # App Password
BACKUP_EMAIL   = os.environ.get('BACKUP_EMAIL', GMAIL_USER)
KEEP_DAYS      = int(os.environ.get('BACKUP_KEEP_DAYS', '7'))

# ── Dump ──────────────────────────────────────────────────────────────────

def run_dump() -> Path:
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    raw_path  = BACKUP_DIR / f"winery_{ts}.sql"
    gz_path   = BACKUP_DIR / f"winery_{ts}.sql.gz"

    log.info(f"Avvio pg_dump → {raw_path}")
    env = os.environ.copy()
    env['PGPASSWORD'] = DB_PASSWORD

    result = subprocess.run(
        [
            'pg_dump',
            '-h', DB_HOST,
            '-p', DB_PORT,
            '-U', DB_USER,
            '-d', DB_NAME,
            '--no-owner',
            '--no-acl',
            '-f', str(raw_path),
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"pg_dump fallito:\n{result.stderr}")

    log.info(f"Compressione → {gz_path}")
    with open(raw_path, 'rb') as f_in, gzip.open(gz_path, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
    raw_path.unlink()

    size_mb = gz_path.stat().st_size / 1024 / 1024
    log.info(f"Dump creato: {gz_path.name} ({size_mb:.2f} MB)")
    return gz_path

# ── Invio Gmail ───────────────────────────────────────────────────────────

def send_gmail(gz_path: Path):
    log.info(f"Invio backup a {BACKUP_EMAIL} via Gmail SMTP...")

    msg = MIMEMultipart()
    msg['From']    = GMAIL_USER
    msg['To']      = BACKUP_EMAIL
    msg['Subject'] = f"[VinoManager] Backup DB — {datetime.now().strftime('%d/%m/%Y %H:%M')}"

    body = (
        f"Backup automatico VinoManager\n\n"
        f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
        f"DB: {DB_NAME}@{DB_HOST}\n"
        f"File: {gz_path.name}\n"
        f"Dimensione: {gz_path.stat().st_size / 1024 / 1024:.2f} MB\n\n"
        "Il file è allegato come archivio .sql.gz.\n"
        "Per ripristinare: gunzip backup.sql.gz && psql -U user -d db < backup.sql"
    )
    msg.attach(MIMEText(body, 'plain'))

    with open(gz_path, 'rb') as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header(
        'Content-Disposition',
        f'attachment; filename="{gz_path.name}"',
    )
    msg.attach(part)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.send_message(msg)

    log.info("Email inviata correttamente")

# ── Pulizia backup vecchi ──────────────────────────────────────────────────

def cleanup_old_backups():
    cutoff = datetime.now() - timedelta(days=KEEP_DAYS)
    for f in BACKUP_DIR.glob('winery_*.sql.gz'):
        ts_str = f.stem.replace('winery_', '').replace('.sql', '')
        try:
            file_dt = datetime.strptime(ts_str, '%Y%m%d_%H%M%S')
            if file_dt < cutoff:
                f.unlink()
                log.info(f"Rimosso backup vecchio: {f.name}")
        except ValueError:
            pass

# ── Main ──────────────────────────────────────────────────────────────────

def main():
    log.info("=== Avvio procedura di backup ===")
    try:
        gz_path = run_dump()
        send_gmail(gz_path)
        cleanup_old_backups()
        log.info("=== Backup completato con successo ===")
    except Exception as e:
        log.error(f"ERRORE durante il backup: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
