"""
Dashboard Ordini — endpoint specializzati per le 5 sotto-dashboard:

  1. Commerciale generale
  2. Clienti
  3. Agenti
  4. Prodotti / Vini
  5. Pagamenti

Tutti gli endpoint:
  - usano ESCLUSIVAMENTE dati registrati negli ordini (modello Ordine + righe);
  - considerano solo ordini in stato CONFERMATO (gli ANNULLATI sono esclusi);
  - accettano gli stessi filtri globali via query-string:
      periodo = oggi | settimana | mese | trimestre | semestre | anno | personalizzato
      date_from, date_to       (richiesti solo se periodo=personalizzato, formato ISO YYYY-MM-DD)
      cliente_id, agente_id
      paese_id, regione_id, provincia_id
      famiglia_id, tipologia_id
"""

from decimal import Decimal
from datetime import datetime, timedelta, time

from django.db.models import Q
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import (
    Ordine, RigaOrdineBottiglia,
    Cliente, Agente,
    Paese, Regione, Provincia,
    FamigliaVino, TipologiaVino,
)


# ─── Helpers periodo & filtri ─────────────────────────────────────────────

def _start_of_day(dt):
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def _next_month(d):
    """Primo giorno del mese successivo a `d` (datetime aware)."""
    if d.month == 12:
        return d.replace(year=d.year + 1, month=1, day=1)
    return d.replace(month=d.month + 1, day=1)


def _parse_periodo(request):
    """
    Ritorna una tupla (date_from, date_to) con datetime aware (timezone della config Django).
    Lo schema delle finestre è semi-aperto: [date_from, date_to).
    Se non viene specificato alcun periodo (o periodo invalido) ritorna (None, None)
    e il filtro temporale non viene applicato.
    """
    now = timezone.localtime()
    today_start = _start_of_day(now)
    periodo = (request.GET.get('periodo') or '').strip().lower()

    date_from = None
    date_to = None

    if periodo == 'oggi':
        date_from = today_start
        date_to = today_start + timedelta(days=1)

    elif periodo == 'settimana':
        # settimana lunedì-domenica (ISO): weekday() Mon=0 … Sun=6
        days_since_monday = today_start.weekday()
        date_from = today_start - timedelta(days=days_since_monday)
        date_to = date_from + timedelta(days=7)

    elif periodo == 'mese':
        date_from = today_start.replace(day=1)
        date_to = _next_month(date_from)

    elif periodo == 'trimestre':
        q_start_month = ((today_start.month - 1) // 3) * 3 + 1
        date_from = today_start.replace(month=q_start_month, day=1)
        # +3 mesi
        d = date_from
        for _ in range(3):
            d = _next_month(d)
        date_to = d

    elif periodo == 'semestre':
        s_start_month = 1 if today_start.month <= 6 else 7
        date_from = today_start.replace(month=s_start_month, day=1)
        if s_start_month == 1:
            date_to = today_start.replace(month=7, day=1)
        else:
            date_to = today_start.replace(year=today_start.year + 1, month=1, day=1)

    elif periodo == 'anno':
        date_from = today_start.replace(month=1, day=1)
        date_to = today_start.replace(year=today_start.year + 1, month=1, day=1)

    elif periodo == 'personalizzato':
        df = request.GET.get('date_from')
        dt_ = request.GET.get('date_to')
        try:
            if df:
                d = datetime.fromisoformat(df)
                date_from = timezone.make_aware(datetime.combine(d.date(), time.min))
        except (ValueError, TypeError):
            date_from = None
        try:
            if dt_:
                d = datetime.fromisoformat(dt_)
                # finestra inclusiva sul giorno finale: aggiungiamo 1 giorno
                date_to = timezone.make_aware(datetime.combine(d.date(), time.min)) + timedelta(days=1)
        except (ValueError, TypeError):
            date_to = None

    return date_from, date_to


def _filtered_ordini(request, *, only_confermato=True, ignore_periodo=False):
    """Queryset di Ordine filtrato in base ai filtri globali del request."""
    qs = (
        Ordine.objects.all()
        .select_related('cliente', 'agente',
                        'cliente__paese', 'cliente__regione', 'cliente__provincia')
        .prefetch_related('righe_bottiglie__tipologia_vino__famiglia')
    )

    if only_confermato:
        qs = qs.filter(stato=Ordine.Stato.CONFERMATO)

    if not ignore_periodo:
        date_from, date_to = _parse_periodo(request)
        if date_from is not None:
            qs = qs.filter(data__gte=date_from)
        if date_to is not None:
            qs = qs.filter(data__lt=date_to)

    def _arg(*keys):
        for k in keys:
            v = request.GET.get(k)
            if v not in (None, '', 'null', 'undefined'):
                return v
        return None

    cliente_id = _arg('cliente_id', 'cliente')
    if cliente_id:
        qs = qs.filter(cliente_id=cliente_id)

    agente_id = _arg('agente_id', 'agente')
    if agente_id:
        qs = qs.filter(agente_id=agente_id)

    paese_id = _arg('paese_id', 'paese')
    if paese_id:
        qs = qs.filter(cliente__paese_id=paese_id)

    regione_id = _arg('regione_id', 'regione')
    if regione_id:
        qs = qs.filter(cliente__regione_id=regione_id)

    provincia_id = _arg('provincia_id', 'provincia')
    if provincia_id:
        qs = qs.filter(cliente__provincia_id=provincia_id)

    famiglia_id = _arg('famiglia_id', 'famiglia')
    if famiglia_id:
        qs = qs.filter(
            righe_bottiglie__tipologia_vino__famiglia_id=famiglia_id
        ).distinct()

    tipologia_id = _arg('tipologia_id', 'tipologia')
    if tipologia_id:
        qs = qs.filter(righe_bottiglie__tipologia_vino_id=tipologia_id).distinct()

    return qs


# ─── Calcoli totali ───────────────────────────────────────────────────────

def _totals_for_order(o, *, restrict_filter=None):
    """
    Calcola i totali per un singolo ordine (già con righe prefetchate).
    `restrict_filter` è una funzione opzionale (riga -> bool) per restringere
    le righe considerate (utile per la dashboard prodotti con filtro famiglia/tipologia).
    Ritorna un dict con imp_lordo, imp_netto, totale (IVA incl), bottiglie.

    Convenzione: applichiamo lo sconto dell'ordine in modo proporzionale anche quando
    contiamo solo un sotto-insieme di righe (è la stessa logica usata nel modello).
    """
    imp_lordo = Decimal('0')
    bottiglie = 0
    for r in o.righe_bottiglie.all():
        if restrict_filter and not restrict_filter(r):
            continue
        imp_lordo += Decimal(r.quantita) * r.prezzo_unitario
        bottiglie += r.quantita

    sconto = o.sconto_percentuale or Decimal('0')
    aliquota = o.aliquota_iva or Decimal('0')
    imp_netto = (imp_lordo * (Decimal('100') - sconto) / Decimal('100'))
    totale = (imp_netto * (Decimal('100') + aliquota) / Decimal('100'))

    return {
        'imp_lordo': imp_lordo.quantize(Decimal('0.01')),
        'imp_netto': imp_netto.quantize(Decimal('0.01')),
        'totale': totale.quantize(Decimal('0.01')),
        'bottiglie': bottiglie,
    }


def _matches_product_filters(riga, request):
    """True se la riga rispetta i filtri famiglia/tipologia/etichetta dal request."""
    famiglia_id = request.GET.get('famiglia_id') or request.GET.get('famiglia')
    if famiglia_id:
        try:
            if riga.tipologia_vino.famiglia_id != int(famiglia_id):
                return False
        except (ValueError, TypeError):
            pass

    tipologia_id = request.GET.get('tipologia_id') or request.GET.get('tipologia')
    if tipologia_id:
        try:
            if riga.tipologia_vino_id != int(tipologia_id):
                return False
        except (ValueError, TypeError):
            pass

    etichettato = (request.GET.get('etichettato') or '').strip().lower()
    if etichettato in ('1', 'true', 'si', 'sì', 'yes'):
        if not riga.ha_etichetta:
            return False
    elif etichettato in ('0', 'false', 'no'):
        if riga.ha_etichetta:
            return False
    return True


# ─── Opzioni per i filtri ─────────────────────────────────────────────────

@api_view(['GET'])
def dashboard_ordini_filtri(request):
    """Ritorna le liste necessarie a popolare i filtri globali del frontend."""
    return Response({
        'clienti': list(
            Cliente.objects.values('id', 'nome', 'azienda',
                                   'paese_id', 'regione_id', 'provincia_id')
                            .order_by('azienda', 'nome')
        ),
        'agenti': list(
            Agente.objects.values('id', 'nome', 'cognome')
                          .order_by('cognome', 'nome')
        ),
        'paesi': list(Paese.objects.values('id', 'nome').order_by('nome')),
        'regioni': list(
            Regione.objects.values('id', 'nome', 'paese_id').order_by('nome')
        ),
        'province': list(
            Provincia.objects.values('id', 'nome', 'sigla', 'regione_id').order_by('nome')
        ),
        'famiglie_vino': list(
            FamigliaVino.objects.values('id', 'nome').order_by('nome')
        ),
        'tipologie_vino': list(
            TipologiaVino.objects.values('id', 'nome', 'famiglia_id', 'famiglia__nome')
                                 .order_by('famiglia__nome', 'nome')
        ),
    })


# ─── Dashboard 1: Commerciale Generale ────────────────────────────────────

@api_view(['GET'])
def dashboard_ordini_commerciale(request):
    """
    Dashboard 1 — Commerciale Generale (home).

    KPI FISSI (non dipendono dai filtri di periodo, dipendono dagli altri filtri):
      - Fatturato mese corrente / anno corrente
      - Numero ordini mese / anno
      - Bottiglie vendute mese / anno

    KPI sul periodo selezionato (rispettano TUTTI i filtri inclusi periodo):
      - Fatturato, n. ordini, bottiglie nel periodo
      - % ordini pagati / non pagati

    + serie storica fatturato per mese (anno corrente).
    """
    # --- Periodo selezionato ----------------------------------------------
    qs_periodo = _filtered_ordini(request)

    fatturato_p = Decimal('0')
    bottiglie_p = 0
    n_ordini_p = 0
    n_pagati_p = 0
    for o in qs_periodo:
        t = _totals_for_order(o)
        fatturato_p += t['imp_netto']
        bottiglie_p += t['bottiglie']
        n_ordini_p += 1
        if o.fattura_pagata:
            n_pagati_p += 1
    n_non_pagati_p = n_ordini_p - n_pagati_p
    perc_pagati = (Decimal(n_pagati_p) / Decimal(n_ordini_p) * Decimal('100')) if n_ordini_p else Decimal('0')
    perc_non_pagati = (Decimal('100') - perc_pagati) if n_ordini_p else Decimal('0')

    # --- KPI fissi mese / anno (ignorano il filtro periodo) ---------------
    now = timezone.localtime()
    today_start = _start_of_day(now)
    mese_start = today_start.replace(day=1)
    mese_end = _next_month(mese_start)
    anno_start = today_start.replace(month=1, day=1)
    anno_end = today_start.replace(year=today_start.year + 1, month=1, day=1)

    qs_no_period = _filtered_ordini(request, ignore_periodo=True)

    def _aggregate(qs):
        f = Decimal('0'); b = 0; c = 0
        for ordine in qs:
            t = _totals_for_order(ordine)
            f += t['imp_netto']; b += t['bottiglie']; c += 1
        return f, b, c

    fat_mese, bott_mese, cnt_mese = _aggregate(
        qs_no_period.filter(data__gte=mese_start, data__lt=mese_end)
    )
    fat_anno, bott_anno, cnt_anno = _aggregate(
        qs_no_period.filter(data__gte=anno_start, data__lt=anno_end)
    )

    # --- Trend fatturato per mese (anno corrente) ------------------------
    trend = []
    cursore = anno_start
    while cursore < anno_end:
        next_c = _next_month(cursore)
        f, b, c = _aggregate(
            qs_no_period.filter(data__gte=cursore, data__lt=next_c)
        )
        trend.append({
            'mese': cursore.month,
            'label': cursore.strftime('%b'),
            'fatturato': float(f),
            'bottiglie': b,
            'ordini': c,
        })
        cursore = next_c

    return Response({
        'kpi_fissi': {
            'fatturato_mese': float(fat_mese),
            'fatturato_anno': float(fat_anno),
            'n_ordini_mese': cnt_mese,
            'n_ordini_anno': cnt_anno,
            'bottiglie_mese': bott_mese,
            'bottiglie_anno': bott_anno,
        },
        'periodo': {
            'fatturato': float(fatturato_p),
            'bottiglie': bottiglie_p,
            'n_ordini': n_ordini_p,
            'n_pagati': n_pagati_p,
            'n_non_pagati': n_non_pagati_p,
            'perc_pagati': float(perc_pagati.quantize(Decimal('0.1'))),
            'perc_non_pagati': float(perc_non_pagati.quantize(Decimal('0.1'))),
        },
        'trend_anno': trend,
    })


# ─── Dashboard 2: Clienti ─────────────────────────────────────────────────

@api_view(['GET'])
def dashboard_ordini_clienti(request):
    """
    Dashboard 2 — Clienti.

    Filtri: cliente, paese, regione, provincia, periodo (gestiti centralmente).

    Restituisce un'aggregazione PER CLIENTE con:
      fatturato, numero_ordini, bottiglie_acquistate, valore_medio_ordine,
      ultimo_ordine (data ISO).

    Più i KPI complessivi del periodo.
    """
    qs = _filtered_ordini(request)

    bucket = {}  # cliente_id -> aggregati
    for o in qs:
        c_id = o.cliente_id
        if c_id not in bucket:
            bucket[c_id] = {
                'cliente_id': c_id,
                'cliente': str(o.cliente) if o.cliente else '—',
                'azienda': o.cliente.azienda if o.cliente else '',
                'paese': (o.cliente.paese.nome if o.cliente and o.cliente.paese else ''),
                'regione': (o.cliente.regione.nome if o.cliente and o.cliente.regione else ''),
                'provincia': (o.cliente.provincia.nome if o.cliente and o.cliente.provincia else ''),
                'fatturato': Decimal('0'),
                'numero_ordini': 0,
                'bottiglie': 0,
                'ultimo_ordine': None,
            }
        t = _totals_for_order(o)
        b = bucket[c_id]
        b['fatturato'] += t['imp_netto']
        b['bottiglie'] += t['bottiglie']
        b['numero_ordini'] += 1
        if not b['ultimo_ordine'] or o.data > b['ultimo_ordine']:
            b['ultimo_ordine'] = o.data

    rows = []
    tot_fat = Decimal('0'); tot_bott = 0; tot_ord = 0
    for b in bucket.values():
        vm = (b['fatturato'] / Decimal(b['numero_ordini'])) if b['numero_ordini'] else Decimal('0')
        rows.append({
            'cliente_id': b['cliente_id'],
            'cliente': b['cliente'],
            'azienda': b['azienda'],
            'paese': b['paese'],
            'regione': b['regione'],
            'provincia': b['provincia'],
            'fatturato': float(b['fatturato'].quantize(Decimal('0.01'))),
            'numero_ordini': b['numero_ordini'],
            'bottiglie': b['bottiglie'],
            'valore_medio_ordine': float(vm.quantize(Decimal('0.01'))),
            'ultimo_ordine': b['ultimo_ordine'].isoformat() if b['ultimo_ordine'] else None,
        })
        tot_fat += b['fatturato']; tot_bott += b['bottiglie']; tot_ord += b['numero_ordini']

    rows.sort(key=lambda r: r['fatturato'], reverse=True)

    return Response({
        'totali': {
            'fatturato': float(tot_fat.quantize(Decimal('0.01'))),
            'bottiglie': tot_bott,
            'n_ordini': tot_ord,
            'n_clienti': len(rows),
            'valore_medio_ordine': float((tot_fat / Decimal(tot_ord)).quantize(Decimal('0.01'))) if tot_ord else 0.0,
        },
        'clienti': rows,
    })


# ─── Dashboard 3: Agenti ──────────────────────────────────────────────────

@api_view(['GET'])
def dashboard_ordini_agenti(request):
    """
    Dashboard 3 — Agenti. Filtro: periodo (e gli altri globali).

    KPI per ogni agente: fatturato, bottiglie, n. ordini.
    + Classifiche (top per fatturato, top per bottiglie, top per ordini).
    """
    qs = _filtered_ordini(request)

    bucket = {}
    senza_agente = {
        'agente_id': None,
        'agente': 'Senza agente',
        'fatturato': Decimal('0'),
        'bottiglie': 0,
        'numero_ordini': 0,
    }

    for o in qs:
        t = _totals_for_order(o)
        if o.agente_id is None:
            target = senza_agente
        else:
            target = bucket.setdefault(o.agente_id, {
                'agente_id': o.agente_id,
                'agente': str(o.agente) if o.agente else '—',
                'fatturato': Decimal('0'),
                'bottiglie': 0,
                'numero_ordini': 0,
            })
        target['fatturato'] += t['imp_netto']
        target['bottiglie'] += t['bottiglie']
        target['numero_ordini'] += 1

    def _row(b):
        return {
            'agente_id': b['agente_id'],
            'agente': b['agente'],
            'fatturato': float(b['fatturato'].quantize(Decimal('0.01'))),
            'bottiglie': b['bottiglie'],
            'numero_ordini': b['numero_ordini'],
        }

    rows = [_row(b) for b in bucket.values()]
    if senza_agente['numero_ordini'] > 0:
        rows.append(_row(senza_agente))

    classifica_fatturato = sorted(rows, key=lambda r: r['fatturato'], reverse=True)
    classifica_bottiglie = sorted(rows, key=lambda r: r['bottiglie'], reverse=True)
    classifica_ordini = sorted(rows, key=lambda r: r['numero_ordini'], reverse=True)

    tot_fat = sum((r['fatturato'] for r in rows), 0.0)
    tot_bott = sum((r['bottiglie'] for r in rows), 0)
    tot_ord = sum((r['numero_ordini'] for r in rows), 0)

    return Response({
        'totali': {
            'fatturato': round(tot_fat, 2),
            'bottiglie': tot_bott,
            'n_ordini': tot_ord,
            'n_agenti': len(bucket),
        },
        'agenti': classifica_fatturato,
        'classifica_fatturato': classifica_fatturato[:10],
        'classifica_bottiglie': classifica_bottiglie[:10],
        'classifica_ordini': classifica_ordini[:10],
        'miglior_agente_fatturato': classifica_fatturato[0] if classifica_fatturato else None,
        'miglior_agente_bottiglie': classifica_bottiglie[0] if classifica_bottiglie else None,
        'miglior_agente_ordini': classifica_ordini[0] if classifica_ordini else None,
    })


# ─── Dashboard 4: Prodotti / Vini ─────────────────────────────────────────

@api_view(['GET'])
def dashboard_ordini_prodotti(request):
    """
    Dashboard 4 — Prodotti / Vini.

    Filtri specifici: famiglia_vino, tipologia_vino, etichettato (true/false),
    più i filtri globali.

    Per ogni tipologia di vino: bottiglie vendute, fatturato generato (proporzionale
    allo sconto dell'ordine), nr. di ordini in cui è presente.
    Più aggregazione per famiglia.
    """
    qs = _filtered_ordini(request)

    by_tip = {}
    by_fam = {}

    for o in qs:
        sconto = o.sconto_percentuale or Decimal('0')
        coeff_sconto = (Decimal('100') - sconto) / Decimal('100')

        # raccogliamo le righe che superano i filtri prodotto
        righe_ok = [r for r in o.righe_bottiglie.all() if _matches_product_filters(r, request)]
        if not righe_ok:
            continue

        # per ogni tipologia
        tip_seen_in_order = set()
        fam_seen_in_order = set()
        for r in righe_ok:
            tv = r.tipologia_vino
            fam = tv.famiglia

            sub_lordo = Decimal(r.quantita) * r.prezzo_unitario
            sub_netto = (sub_lordo * coeff_sconto).quantize(Decimal('0.01'))

            t = by_tip.setdefault(tv.id, {
                'tipologia_id': tv.id,
                'tipologia': tv.nome,
                'famiglia_id': fam.id,
                'famiglia': fam.nome,
                'bottiglie': 0,
                'fatturato': Decimal('0'),
                'n_ordini': 0,
            })
            t['bottiglie'] += r.quantita
            t['fatturato'] += sub_netto
            if tv.id not in tip_seen_in_order:
                t['n_ordini'] += 1
                tip_seen_in_order.add(tv.id)

            f = by_fam.setdefault(fam.id, {
                'famiglia_id': fam.id,
                'famiglia': fam.nome,
                'bottiglie': 0,
                'fatturato': Decimal('0'),
                'n_ordini': 0,
            })
            f['bottiglie'] += r.quantita
            f['fatturato'] += sub_netto
            if fam.id not in fam_seen_in_order:
                f['n_ordini'] += 1
                fam_seen_in_order.add(fam.id)

    def _fmt(d):
        return {**d, 'fatturato': float(d['fatturato'].quantize(Decimal('0.01')))}

    prodotti = sorted((_fmt(v) for v in by_tip.values()),
                      key=lambda r: r['fatturato'], reverse=True)
    famiglie = sorted((_fmt(v) for v in by_fam.values()),
                      key=lambda r: r['fatturato'], reverse=True)

    tot_fat = sum((r['fatturato'] for r in prodotti), 0.0)
    tot_bott = sum((r['bottiglie'] for r in prodotti), 0)

    return Response({
        'totali': {
            'fatturato': round(tot_fat, 2),
            'bottiglie': tot_bott,
            'n_tipologie': len(prodotti),
            'n_famiglie': len(famiglie),
        },
        'prodotti': prodotti,
        'famiglie': famiglie,
    })


# ─── Dashboard 5: Pagamenti ───────────────────────────────────────────────

@api_view(['GET'])
def dashboard_ordini_pagamenti(request):
    """
    Dashboard 5 — Pagamenti. Filtri globali.

    KPI:
      - Numero ordini pagati
      - Numero ordini non pagati
      - Totale incassato (= somma dei totali IVA inclusa degli ordini PAGATI)
      - Totale da incassare (= somma dei totali IVA inclusa degli ordini NON PAGATI)
    """
    qs = _filtered_ordini(request)

    n_pagati = 0
    n_non_pagati = 0
    incassato = Decimal('0')          # totale (IVA incl) ordini pagati
    da_incassare = Decimal('0')       # totale (IVA incl) ordini non pagati
    fatturato_pagati = Decimal('0')   # imponibile netto ordini pagati
    fatturato_non_pagati = Decimal('0')

    elenco_da_incassare = []

    for o in qs:
        t = _totals_for_order(o)
        if o.fattura_pagata:
            n_pagati += 1
            incassato += t['totale']
            fatturato_pagati += t['imp_netto']
        else:
            n_non_pagati += 1
            da_incassare += t['totale']
            fatturato_non_pagati += t['imp_netto']
            elenco_da_incassare.append({
                'ordine_id': o.id,
                'numero': o.numero,
                'data': o.data.isoformat(),
                'cliente': str(o.cliente) if o.cliente else '—',
                'agente': str(o.agente) if o.agente else '',
                'imponibile_netto': float(t['imp_netto']),
                'totale': float(t['totale']),
            })

    elenco_da_incassare.sort(key=lambda r: r['data'])

    return Response({
        'n_pagati': n_pagati,
        'n_non_pagati': n_non_pagati,
        'totale_incassato': float(incassato.quantize(Decimal('0.01'))),
        'totale_da_incassare': float(da_incassare.quantize(Decimal('0.01'))),
        'fatturato_pagati': float(fatturato_pagati.quantize(Decimal('0.01'))),
        'fatturato_non_pagati': float(fatturato_non_pagati.quantize(Decimal('0.01'))),
        'ordini_da_incassare': elenco_da_incassare,
    })
