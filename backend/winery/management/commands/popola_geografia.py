"""
Management command per popolare i dati geografici:
- Italia + Paesi UE principali
- Tutte le regioni, province, comuni e CAP italiani

Uso:
  python manage.py popola_geografia            # esegue solo se vuoto
  python manage.py popola_geografia --force    # ripopola da zero
"""
import json
import os
import urllib.request
from django.core.management.base import BaseCommand
from django.db import transaction
from winery.models import Paese, Regione, Provincia, Citta


URL_COMUNI = "https://raw.githubusercontent.com/matteocontrini/comuni-json/master/comuni.json"

PAESI_EXTRA = [
    ('Austria', 'AT'), ('Belgio', 'BE'), ('Croazia', 'HR'), ('Danimarca', 'DK'),
    ('Estonia', 'EE'), ('Finlandia', 'FI'), ('Francia', 'FR'), ('Germania', 'DE'),
    ('Grecia', 'GR'), ('Irlanda', 'IE'), ('Lettonia', 'LV'), ('Lituania', 'LT'),
    ('Lussemburgo', 'LU'), ('Malta', 'MT'), ('Paesi Bassi', 'NL'), ('Polonia', 'PL'),
    ('Portogallo', 'PT'), ('Regno Unito', 'GB'), ('Repubblica Ceca', 'CZ'),
    ('Romania', 'RO'), ('Slovacchia', 'SK'), ('Slovenia', 'SI'), ('Spagna', 'ES'),
    ('Svezia', 'SE'), ('Svizzera', 'CH'), ('Ungheria', 'HU'), ('Norvegia', 'NO'),
    ('Stati Uniti', 'US'), ('Canada', 'CA'), ('Giappone', 'JP'), ('Cina', 'CN'),
    ('Australia', 'AU'), ('Brasile', 'BR'), ('Argentina', 'AR'),
]


def scarica_comuni():
    cache_path = '/tmp/comuni_italiani.json'
    if os.path.exists(cache_path):
        with open(cache_path, encoding='utf-8') as f:
            return json.load(f)
    try:
        req = urllib.request.Request(URL_COMUNI, headers={'User-Agent': 'VinoManager/1.0'})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception:
            pass
        return data
    except Exception as e:
        raise RuntimeError(
            f"Impossibile scaricare il dataset comuni da {URL_COMUNI}: {e}\n"
            "Verifica la connettività di rete del container."
        )


class Command(BaseCommand):
    help = "Popola Paesi, Regioni, Province, Città e CAP italiani"

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help="Cancella e ripopola")

    def handle(self, *args, **opts):
        force = opts['force']

        if not force and Citta.objects.exists():
            self.stdout.write(self.style.WARNING(
                "Dati geografici già presenti. Usa --force per ripopolare."
            ))
            return

        if force:
            self.stdout.write("Cancellazione dati esistenti...")
            Citta.objects.all().delete()
            Provincia.objects.all().delete()
            Regione.objects.all().delete()
            Paese.objects.all().delete()

        self.stdout.write("Scaricamento dataset comuni italiani...")
        comuni = scarica_comuni()
        self.stdout.write(self.style.SUCCESS(f"  → {len(comuni)} comuni caricati"))

        with transaction.atomic():
            italia, _ = Paese.objects.get_or_create(
                nome='Italia', defaults={'codice_iso': 'IT'},
            )

            for nome_paese, iso in PAESI_EXTRA:
                Paese.objects.get_or_create(
                    nome=nome_paese, defaults={'codice_iso': iso},
                )

            regioni_map = {}
            regioni_uniche = {}
            for c in comuni:
                r = c['regione']
                regioni_uniche[r['nome']] = r['codice']

            for nome_reg, codice_reg in regioni_uniche.items():
                reg = Regione.objects.create(
                    paese=italia, nome=nome_reg, codice_istat=codice_reg,
                )
                regioni_map[nome_reg] = reg
            self.stdout.write(self.style.SUCCESS(f"  → {len(regioni_map)} regioni"))

            province_map = {}
            for c in comuni:
                key = (c['regione']['nome'], c['provincia']['nome'])
                if key not in province_map:
                    prov = Provincia.objects.create(
                        regione=regioni_map[c['regione']['nome']],
                        nome=c['provincia']['nome'] or c['regione']['nome'],
                        sigla=c['sigla'],
                        codice_istat=c['provincia']['codice'],
                    )
                    province_map[key] = prov
            self.stdout.write(self.style.SUCCESS(f"  → {len(province_map)} province"))

            citta_da_creare = []
            for c in comuni:
                key = (c['regione']['nome'], c['provincia']['nome'])
                citta_da_creare.append(Citta(
                    provincia=province_map[key],
                    nome=c['nome'],
                    codice_istat=c['codice'],
                    codice_catastale=c.get('codiceCatastale', ''),
                    cap_list=c.get('cap', []),
                ))
            Citta.objects.bulk_create(citta_da_creare, batch_size=1000)
            self.stdout.write(self.style.SUCCESS(f"  → {len(citta_da_creare)} città"))

        self.stdout.write(self.style.SUCCESS(
            f"\n✓ Dati geografici popolati con successo."
        ))