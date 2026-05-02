# 🍷 VinoManager — Quick Start

Per utenti che hanno già Docker installato.

## Avvio Rapido

```bash
# 1. Estrai
tar -xzf wine-manager.tar.gz
cd wine-manager

# 2. Avvia
docker compose up --build

# 3. Apri browser
http://localhost:5173
```

## Accessi

- **Frontend**: http://localhost:5173
- **Admin Django**: http://localhost:8000/admin/ (admin/admin)
- **API**: http://localhost:8000/api/

## Workflow Base

1. **Configurazione** → Crea tipologie materiali (cartoni, tappi, bottiglie, etichette, capsule, cestelli)
2. **Tipologie Vino** → Crea famiglie e tipologie con materiali associati
3. **Magazzino** → Carica materiali e vino nei silos
4. **Imbottigliamento** → 3 modalità:
   - Crea senza etichetta → step intermedio
   - Crea con etichetta → bottiglia completa
   - Associa etichetta → completa bottiglie esistenti (anche cross-type!)

## Comandi Utili

```bash
# Stop
docker compose down

# Reset totale
docker compose down -v && docker compose up --build

# Backup
docker compose exec backend python manage.py dumpdata > backup.json

# Restore
docker compose exec backend python manage.py loaddata backup.json

# Logs
docker compose logs -f backend
```

## Note Importanti

- Le bottiglie sono aggregate in **lotti** (non 1 riga = 1 bottiglia)
- Associa etichetta permette **cross-type** (bottiglia vino X → etichetta vino Y)
- Flag capsula intelligente: prende prima bottiglie senza capsula se attivo
- Tutti i materiali sono configurabili dall'utente (niente preimpostato)

## Troubleshooting

**Errore "relation does not exist"**:
```bash
docker compose down -v
docker compose up --build
```

**Porta occupata**: Cambia porte in `docker-compose.yml`

Per la guida completa: vedi `GUIDA_INSTALLAZIONE.md`
