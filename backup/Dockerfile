FROM python:3.12-slim

# pg_dump e cron
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    cron \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /backup

COPY backup.py /backup/backup.py
COPY crontab /etc/cron.d/winery-backup

# Permessi corretti per cron
RUN chmod 0644 /etc/cron.d/winery-backup \
    && crontab /etc/cron.d/winery-backup \
    && touch /var/log/backup.log

CMD ["sh", "-c", "printenv | grep -E '^(DB_|GMAIL_|BACKUP_)' > /etc/environment && cron && tail -f /var/log/backup.log"]
