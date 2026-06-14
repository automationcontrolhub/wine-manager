#!/bin/sh
set -e

echo "=== [entrypoint] Avvio container backend ==="

# Attendi che il DB sia pronto (ridondante con healthcheck Docker, ma sicuro)
echo "=== [entrypoint] Attesa DB ==="
until python -c "
import dj_database_url, psycopg2, os
conf = dj_database_url.parse(os.environ['DATABASE_URL'])
conn = psycopg2.connect(
    host=conf['HOST'], port=conf['PORT'] or 5432,
    dbname=conf['NAME'], user=conf['USER'], password=conf['PASSWORD']
)
conn.close()
print('DB OK')
" 2>/dev/null; do
    echo "DB non ancora disponibile, ritento tra 2s..."
    sleep 2
done

echo "=== [entrypoint] Generazione migrazioni ==="
python manage.py makemigrations --no-input

echo "=== [entrypoint] Applica migrazioni ==="
python manage.py migrate --no-input

echo "=== [entrypoint] Raccogli static files ==="
python manage.py collectstatic --no-input --clear

echo "=== [entrypoint] Crea superuser admin ==="
python manage.py create_admin

echo "=== [entrypoint] Avvio Daphne (ASGI) su 0.0.0.0:8000 ==="
exec daphne \
    -b 0.0.0.0 \
    -p 8000 \
    --access-log - \
    --proxy-headers \
    config.asgi:application
