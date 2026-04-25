from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response

from .models import (
    TipoCartone, TipoTappo, TipoBottiglia, TipoEtichetta,
    TipoCapsula, TipoCestello, FamigliaVino, TipologiaVino,
    LottoBottiglie, MovimentoMagazzino,
)
from .serializers import (
    TipoCartoneSerializer, TipoTappoSerializer, TipoBottigliaSerializer,
    TipoEtichettaSerializer, TipoCapsulaSerializer, TipoCestelloSerializer,
    FamigliaVinoSerializer, TipologiaVinoSerializer,
    LottoBottiglieSerializer, MovimentoMagazzinoSerializer,
    CreaBottiglieSenzaEtichettaSerializer, CreaBottiglieConEtichettaSerializer,
    AssociaEtichettaSerializer, AggiuntaVinoSerializer,
    CaricoMagazzinoSerializer,
)


# ─── Materiali ViewSets ───────────────────────────────────────────────────

class TipoCartoneViewSet(viewsets.ModelViewSet):
    queryset = TipoCartone.objects.all()
    serializer_class = TipoCartoneSerializer
    pagination_class = None


class TipoTappoViewSet(viewsets.ModelViewSet):
    queryset = TipoTappo.objects.all()
    serializer_class = TipoTappoSerializer
    pagination_class = None


class TipoBottigliaViewSet(viewsets.ModelViewSet):
    queryset = TipoBottiglia.objects.all()
    serializer_class = TipoBottigliaSerializer
    pagination_class = None


class TipoEtichettaViewSet(viewsets.ModelViewSet):
    queryset = TipoEtichetta.objects.all()
    serializer_class = TipoEtichettaSerializer
    pagination_class = None


class TipoCapsulaViewSet(viewsets.ModelViewSet):
    queryset = TipoCapsula.objects.all()
    serializer_class = TipoCapsulaSerializer
    pagination_class = None


class TipoCestelloViewSet(viewsets.ModelViewSet):
    queryset = TipoCestello.objects.all()
    serializer_class = TipoCestelloSerializer
    pagination_class = None


# ─── Vino ─────────────────────────────────────────────────────────────────

class FamigliaVinoViewSet(viewsets.ModelViewSet):
    queryset = FamigliaVino.objects.all()
    serializer_class = FamigliaVinoSerializer
    pagination_class = None


class TipologiaVinoViewSet(viewsets.ModelViewSet):
    queryset = TipologiaVino.objects.select_related(
        'famiglia', 'tipo_cartone', 'tipo_tappo', 'tipo_bottiglia',
        'tipo_etichetta', 'tipo_capsula', 'tipo_cestello'
    ).all()
    serializer_class = TipologiaVinoSerializer
    pagination_class = None


# ─── Lotti bottiglie ──────────────────────────────────────────────────────

class LottoBottiglieViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LottoBottiglie.objects.select_related(
        'tipologia_vino', 'tipologia_vino__famiglia'
    ).all()
    serializer_class = LottoBottiglieSerializer
    filterset_fields = ['stato', 'tipologia_vino', 'ha_etichetta']


class MovimentoMagazzinoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MovimentoMagazzino.objects.all()
    serializer_class = MovimentoMagazzinoSerializer


# ─── Aggiunta vino al silos ───────────────────────────────────────────────

@api_view(['POST'])
def aggiunta_vino(request):
    """Aggiunge litri di vino a un silos di una tipologia esistente."""
    ser = AggiuntaVinoSerializer(data=request.data)
    ser.is_valid(raise_exception=True)

    try:
        tipologia = TipologiaVino.objects.get(id=ser.validated_data['tipologia_vino_id'])
    except TipologiaVino.DoesNotExist:
        return Response({'error': 'Tipologia non trovata'}, status=404)

    litri = ser.validated_data['litri']

    with transaction.atomic():
        tipologia.quantita_litri += litri
        tipologia.save(update_fields=['quantita_litri'])

        MovimentoMagazzino.objects.create(
            tipo=MovimentoMagazzino.TipoMovimento.AGGIUNTA_VINO,
            categoria=MovimentoMagazzino.Categoria.VINO,
            quantita=litri,
            descrizione=f"Aggiunta {litri}L a {tipologia}",
            riferimento_id=tipologia.id,
            riferimento_tipo='TipologiaVino',
        )

    return Response({'ok': True, 'nuova_quantita_litri': str(tipologia.quantita_litri)})


# ─── Carico magazzino ─────────────────────────────────────────────────────

@api_view(['POST'])
def carico_magazzino(request):
    """Carica materiale in magazzino (tappi, cartoni, bottiglie, ecc.)."""
    ser = CaricoMagazzinoSerializer(data=request.data)
    ser.is_valid(raise_exception=True)

    d = ser.validated_data
    cat = d['categoria']
    tipo_id = d['tipo_id']
    qty = d['quantita']

    MODEL_MAP = {
        'cartone': (TipoCartone, MovimentoMagazzino.Categoria.CARTONE),
        'tappo': (TipoTappo, MovimentoMagazzino.Categoria.TAPPO),
        'bottiglia': (TipoBottiglia, MovimentoMagazzino.Categoria.BOTTIGLIA),
        'etichetta': (TipoEtichetta, MovimentoMagazzino.Categoria.ETICHETTA),
        'capsula': (TipoCapsula, MovimentoMagazzino.Categoria.CAPSULA),
        'cestello': (TipoCestello, MovimentoMagazzino.Categoria.CESTELLO),
    }

    ModelClass, mov_cat = MODEL_MAP[cat]

    try:
        obj = ModelClass.objects.get(id=tipo_id)
    except ModelClass.DoesNotExist:
        return Response({'error': f'Tipo {cat} non trovato'}, status=404)

    with transaction.atomic():
        obj.quantita += qty
        obj.save(update_fields=['quantita'])

        MovimentoMagazzino.objects.create(
            tipo=MovimentoMagazzino.TipoMovimento.CARICO,
            categoria=mov_cat,
            quantita=qty,
            descrizione=f"Carico {qty}× {obj}",
            riferimento_id=obj.id,
            riferimento_tipo=ModelClass.__name__,
        )

    return Response({'ok': True, 'nuova_quantita': obj.quantita})


# ─── Helper: verifica e scala materiali ───────────────────────────────────

def _verifica_materiali(tipologia, quantita, con_etichetta=True, con_capsula=True):
    """Verifica disponibilità materiali e ritorna errori se non sufficienti."""
    errori = []
    is_spumante = tipologia.famiglia.is_spumante
    capacita_bottiglia = tipologia.tipo_bottiglia.capacita_litri
    litri_necessari = Decimal(str(quantita)) * capacita_bottiglia

    # Vino nel silos
    if tipologia.quantita_litri < litri_necessari:
        errori.append(
            f"Vino insufficiente: servono {litri_necessari}L, "
            f"disponibili {tipologia.quantita_litri}L"
        )

    # Bottiglie
    if tipologia.tipo_bottiglia.quantita < quantita:
        errori.append(
            f"Bottiglie '{tipologia.tipo_bottiglia.nome}' insufficienti: "
            f"servono {quantita}, disponibili {tipologia.tipo_bottiglia.quantita}"
        )

    # Tappi
    if tipologia.tipo_tappo.quantita < quantita:
        errori.append(
            f"Tappi '{tipologia.tipo_tappo.nome}' insufficienti: "
            f"servono {quantita}, disponibili {tipologia.tipo_tappo.quantita}"
        )

    # Etichette (se richieste)
    if con_etichetta and tipologia.tipo_etichetta.quantita < quantita:
        errori.append(
            f"Etichette '{tipologia.tipo_etichetta.nome}' insufficienti: "
            f"servono {quantita}, disponibili {tipologia.tipo_etichetta.quantita}"
        )

    # Capsule (se richieste)
    if con_capsula and tipologia.tipo_capsula.quantita < quantita:
        errori.append(
            f"Capsule '{tipologia.tipo_capsula.nome}' insufficienti: "
            f"servono {quantita}, disponibili {tipologia.tipo_capsula.quantita}"
        )

    # Cestello (solo spumante)
    if is_spumante:
        if not tipologia.tipo_cestello:
            errori.append("Cestello non configurato per questa tipologia spumante")
        elif tipologia.tipo_cestello.quantita < quantita:
            errori.append(
                f"Cestelli '{tipologia.tipo_cestello.nome}' insufficienti: "
                f"servono {quantita}, disponibili {tipologia.tipo_cestello.quantita}"
            )

    # Cartoni
    cap = tipologia.tipo_cartone.capacita_bottiglie
    cartoni_necessari = -(-quantita // cap)  # ceil division
    if tipologia.tipo_cartone.quantita < cartoni_necessari:
        errori.append(
            f"Cartoni '{tipologia.tipo_cartone.nome}' insufficienti: "
            f"servono {cartoni_necessari}, disponibili {tipologia.tipo_cartone.quantita}"
        )

    return errori


def _scala_materiali(tipologia, quantita, con_etichetta=True, con_capsula=True):
    """Scala i materiali dal magazzino e crea movimenti."""
    is_spumante = tipologia.famiglia.is_spumante
    capacita_bottiglia = tipologia.tipo_bottiglia.capacita_litri
    litri_necessari = Decimal(str(quantita)) * capacita_bottiglia
    cap = tipologia.tipo_cartone.capacita_bottiglie
    cartoni_necessari = -(-quantita // cap)

    # Scala vino
    tipologia.quantita_litri -= litri_necessari
    tipologia.save(update_fields=['quantita_litri'])
    MovimentoMagazzino.objects.create(
        tipo=MovimentoMagazzino.TipoMovimento.SCARICO,
        categoria=MovimentoMagazzino.Categoria.VINO,
        quantita=litri_necessari,
        descrizione=f"Imbottigliamento {quantita}× {tipologia}",
    )

    # Scala bottiglie
    tipologia.tipo_bottiglia.quantita -= quantita
    tipologia.tipo_bottiglia.save(update_fields=['quantita'])
    MovimentoMagazzino.objects.create(
        tipo=MovimentoMagazzino.TipoMovimento.SCARICO,
        categoria=MovimentoMagazzino.Categoria.BOTTIGLIA,
        quantita=quantita,
        descrizione=f"Bottiglie per {tipologia}",
    )

    # Scala tappi
    tipologia.tipo_tappo.quantita -= quantita
    tipologia.tipo_tappo.save(update_fields=['quantita'])
    MovimentoMagazzino.objects.create(
        tipo=MovimentoMagazzino.TipoMovimento.SCARICO,
        categoria=MovimentoMagazzino.Categoria.TAPPO,
        quantita=quantita,
        descrizione=f"Tappi per {tipologia}",
    )

    # Scala etichette
    if con_etichetta:
        tipologia.tipo_etichetta.quantita -= quantita
        tipologia.tipo_etichetta.save(update_fields=['quantita'])
        MovimentoMagazzino.objects.create(
            tipo=MovimentoMagazzino.TipoMovimento.SCARICO,
            categoria=MovimentoMagazzino.Categoria.ETICHETTA,
            quantita=quantita,
            descrizione=f"Etichette per {tipologia}",
        )

    # Scala capsule
    if con_capsula:
        tipologia.tipo_capsula.quantita -= quantita
        tipologia.tipo_capsula.save(update_fields=['quantita'])
        MovimentoMagazzino.objects.create(
            tipo=MovimentoMagazzino.TipoMovimento.SCARICO,
            categoria=MovimentoMagazzino.Categoria.CAPSULA,
            quantita=quantita,
            descrizione=f"Capsule per {tipologia}",
        )

    # Scala cestelli (spumante)
    if is_spumante and tipologia.tipo_cestello:
        tipologia.tipo_cestello.quantita -= quantita
        tipologia.tipo_cestello.save(update_fields=['quantita'])
        MovimentoMagazzino.objects.create(
            tipo=MovimentoMagazzino.TipoMovimento.SCARICO,
            categoria=MovimentoMagazzino.Categoria.CESTELLO,
            quantita=quantita,
            descrizione=f"Cestelli per {tipologia}",
        )

    # Scala cartoni
    tipologia.tipo_cartone.quantita -= cartoni_necessari
    tipologia.tipo_cartone.save(update_fields=['quantita'])
    MovimentoMagazzino.objects.create(
        tipo=MovimentoMagazzino.TipoMovimento.SCARICO,
        categoria=MovimentoMagazzino.Categoria.CARTONE,
        quantita=cartoni_necessari,
        descrizione=f"Cartoni per {tipologia}",
    )


# ─── Creazione bottiglie SENZA etichetta ──────────────────────────────────

@api_view(['POST'])
def crea_bottiglie_senza_etichetta(request):
    ser = CreaBottiglieSenzaEtichettaSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    d = ser.validated_data

    try:
        tipologia = TipologiaVino.objects.select_related(
            'famiglia', 'tipo_cartone', 'tipo_tappo', 'tipo_bottiglia',
            'tipo_etichetta', 'tipo_capsula', 'tipo_cestello'
        ).get(id=d['tipologia_vino_id'])
    except TipologiaVino.DoesNotExist:
        return Response({'error': 'Tipologia non trovata'}, status=404)

    quantita = d['quantita']
    con_capsula = d['con_capsula']

    # Verifica materiali (senza etichetta)
    errori = _verifica_materiali(tipologia, quantita, con_etichetta=False, con_capsula=con_capsula)
    if errori:
        return Response({'errors': errori}, status=400)

    with transaction.atomic():
        _scala_materiali(tipologia, quantita, con_etichetta=False, con_capsula=con_capsula)

        # Cerca lotto esistente con stesse caratteristiche per aggregare
        lotto_esistente = LottoBottiglie.objects.filter(
            tipologia_vino=tipologia,
            stato=LottoBottiglie.Stato.SENZA_ETICHETTA,
            ha_etichetta=False,
            ha_capsula=con_capsula,
        ).first()

        if lotto_esistente:
            lotto_esistente.quantita += quantita
            lotto_esistente.save(update_fields=['quantita', 'data_aggiornamento'])
            lotto = lotto_esistente
        else:
            lotto = LottoBottiglie.objects.create(
                tipologia_vino=tipologia,
                quantita=quantita,
                stato=LottoBottiglie.Stato.SENZA_ETICHETTA,
                ha_etichetta=False,
                ha_capsula=con_capsula,
            )

    return Response(LottoBottiglieSerializer(lotto).data, status=201)


# ─── Creazione bottiglie CON etichetta ────────────────────────────────────

@api_view(['POST'])
def crea_bottiglie_con_etichetta(request):
    ser = CreaBottiglieConEtichettaSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    d = ser.validated_data

    try:
        tipologia = TipologiaVino.objects.select_related(
            'famiglia', 'tipo_cartone', 'tipo_tappo', 'tipo_bottiglia',
            'tipo_etichetta', 'tipo_capsula', 'tipo_cestello'
        ).get(id=d['tipologia_vino_id'])
    except TipologiaVino.DoesNotExist:
        return Response({'error': 'Tipologia non trovata'}, status=404)

    quantita = d['quantita']
    con_capsula = d['con_capsula']

    errori = _verifica_materiali(tipologia, quantita, con_etichetta=True, con_capsula=con_capsula)
    if errori:
        return Response({'errors': errori}, status=400)

    with transaction.atomic():
        _scala_materiali(tipologia, quantita, con_etichetta=True, con_capsula=con_capsula)

        lotto_esistente = LottoBottiglie.objects.filter(
            tipologia_vino=tipologia,
            stato=LottoBottiglie.Stato.COMPLETA,
            ha_etichetta=True,
            ha_capsula=con_capsula,
        ).first()

        if lotto_esistente:
            lotto_esistente.quantita += quantita
            lotto_esistente.save(update_fields=['quantita', 'data_aggiornamento'])
            lotto = lotto_esistente
        else:
            lotto = LottoBottiglie.objects.create(
                tipologia_vino=tipologia,
                quantita=quantita,
                stato=LottoBottiglie.Stato.COMPLETA,
                ha_etichetta=True,
                ha_capsula=con_capsula,
            )

    return Response(LottoBottiglieSerializer(lotto).data, status=201)


# ─── Associa etichetta a bottiglie senza etichetta ────────────────────────

@api_view(['POST'])
def associa_etichetta(request):
    """
    Prende N bottiglie SENZA_ETICHETTA di una tipologia ORIGINE,
    scala la quantità dal lotto senza etichetta origine,
    applica l'etichetta della tipologia DESTINAZIONE (può essere diversa!),
    e aggiunge al lotto COMPLETA con tipologia destinazione.
    Scala etichette della destinazione (e opzionalmente capsule se non c'erano).
    
    LOGICA INTELLIGENTE PER CAPSULE:
    - Se con_capsula=True → prendi PRIMA dai lotti SENZA capsula (aggiungi capsula)
    - Se con_capsula=False → prendi PRIMA dai lotti CON capsula (non sprecare capsule)
    """
    ser = AssociaEtichettaSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    d = ser.validated_data

    try:
        tipologia_origine = TipologiaVino.objects.select_related(
            'famiglia', 'tipo_cartone', 'tipo_tappo', 'tipo_bottiglia',
            'tipo_etichetta', 'tipo_capsula', 'tipo_cestello'
        ).get(id=d['tipologia_vino_origine_id'])
    except TipologiaVino.DoesNotExist:
        return Response({'error': 'Tipologia origine non trovata'}, status=404)

    try:
        tipologia_dest = TipologiaVino.objects.select_related(
            'famiglia', 'tipo_cartone', 'tipo_tappo', 'tipo_bottiglia',
            'tipo_etichetta', 'tipo_capsula', 'tipo_cestello'
        ).get(id=d['tipologia_vino_destinazione_id'])
    except TipologiaVino.DoesNotExist:
        return Response({'error': 'Tipologia destinazione non trovata'}, status=404)

    quantita = d['quantita']
    con_capsula = d['con_capsula']

    # Trova bottiglie senza etichetta della tipologia ORIGINE
    # Ordine intelligente basato sul flag con_capsula
    if con_capsula:
        # Se vogliamo aggiungere capsula, prendiamo PRIMA quelle senza
        lotti_senza = LottoBottiglie.objects.filter(
            tipologia_vino=tipologia_origine,
            stato=LottoBottiglie.Stato.SENZA_ETICHETTA,
            ha_etichetta=False,
        ).order_by('ha_capsula', 'data_creazione')  # False prima (senza capsula)
    else:
        # Se NON vogliamo capsula, prendiamo PRIMA quelle che già ce l'hanno
        lotti_senza = LottoBottiglie.objects.filter(
            tipologia_vino=tipologia_origine,
            stato=LottoBottiglie.Stato.SENZA_ETICHETTA,
            ha_etichetta=False,
        ).order_by('-ha_capsula', 'data_creazione')  # True prima (con capsula)

    totale_disponibile = sum(l.quantita for l in lotti_senza)
    if totale_disponibile < quantita:
        return Response({
            'errors': [
                f"Bottiglie senza etichetta insufficienti per {tipologia_origine}: "
                f"servono {quantita}, disponibili {totale_disponibile}"
            ]
        }, status=400)

    # Verifica materiali della tipologia DESTINAZIONE (etichetta e opzionalmente capsule)
    errori = []
    if tipologia_dest.tipo_etichetta.quantita < quantita:
        errori.append(
            f"Etichette '{tipologia_dest.tipo_etichetta.nome}' insufficienti: "
            f"servono {quantita}, disponibili {tipologia_dest.tipo_etichetta.quantita}"
        )

    # Conta quante capsule servono davvero
    # Solo le bottiglie SENZA capsula che vogliamo trasformare IN con capsula
    capsule_da_aggiungere = 0
    if con_capsula:
        rimanenti = quantita
        for lotto in lotti_senza:
            if rimanenti <= 0:
                break
            da_prendere = min(rimanenti, lotto.quantita)
            if not lotto.ha_capsula:
                capsule_da_aggiungere += da_prendere
            rimanenti -= da_prendere

        if capsule_da_aggiungere > 0 and tipologia_dest.tipo_capsula.quantita < capsule_da_aggiungere:
            errori.append(
                f"Capsule '{tipologia_dest.tipo_capsula.nome}' insufficienti: "
                f"servono {capsule_da_aggiungere}, disponibili {tipologia_dest.tipo_capsula.quantita}"
            )

    if errori:
        return Response({'errors': errori}, status=400)

    with transaction.atomic():
        # Scala etichette della DESTINAZIONE
        tipologia_dest.tipo_etichetta.quantita -= quantita
        tipologia_dest.tipo_etichetta.save(update_fields=['quantita'])
        MovimentoMagazzino.objects.create(
            tipo=MovimentoMagazzino.TipoMovimento.SCARICO,
            categoria=MovimentoMagazzino.Categoria.ETICHETTA,
            quantita=quantita,
            descrizione=f"Etichette '{tipologia_dest.tipo_etichetta.nome}' associate a bottiglie (origine: {tipologia_origine}, dest: {tipologia_dest})",
        )

        # Scala capsule della DESTINAZIONE se necessario
        if capsule_da_aggiungere > 0:
            tipologia_dest.tipo_capsula.quantita -= capsule_da_aggiungere
            tipologia_dest.tipo_capsula.save(update_fields=['quantita'])
            MovimentoMagazzino.objects.create(
                tipo=MovimentoMagazzino.TipoMovimento.SCARICO,
                categoria=MovimentoMagazzino.Categoria.CAPSULA,
                quantita=capsule_da_aggiungere,
                descrizione=f"Capsule '{tipologia_dest.tipo_capsula.nome}' associate (step etichetta)",
            )

        # Scala dai lotti senza etichetta della ORIGINE
        # L'ordinamento già fatto garantisce che prendiamo nel giusto ordine
        rimanenti = quantita
        for lotto in lotti_senza:
            if rimanenti <= 0:
                break
            da_prendere = min(rimanenti, lotto.quantita)
            lotto.quantita -= da_prendere
            if lotto.quantita == 0:
                lotto.delete()
            else:
                lotto.save(update_fields=['quantita', 'data_aggiornamento'])
            rimanenti -= da_prendere

        # Aggiungi al lotto completo con tipologia DESTINAZIONE
        lotto_completo = LottoBottiglie.objects.filter(
            tipologia_vino=tipologia_dest,
            stato=LottoBottiglie.Stato.COMPLETA,
            ha_etichetta=True,
            ha_capsula=con_capsula,
        ).first()

        if lotto_completo:
            lotto_completo.quantita += quantita
            lotto_completo.save(update_fields=['quantita', 'data_aggiornamento'])
        else:
            lotto_completo = LottoBottiglie.objects.create(
                tipologia_vino=tipologia_dest,
                quantita=quantita,
                stato=LottoBottiglie.Stato.COMPLETA,
                ha_etichetta=True,
                ha_capsula=con_capsula,
            )

    return Response(LottoBottiglieSerializer(lotto_completo).data, status=200)


# ─── Dashboard / riepilogo ────────────────────────────────────────────────

@api_view(['GET'])
def dashboard(request):
    """Riepilogo generale per la dashboard."""
    # Magazzino materiali
    magazzino = {
        'cartoni': list(TipoCartone.objects.values('id', 'nome', 'capacita_bottiglie', 'quantita')),
        'tappi': list(TipoTappo.objects.values('id', 'nome', 'quantita')),
        'bottiglie': list(TipoBottiglia.objects.values('id', 'nome', 'capacita_litri', 'quantita')),
        'etichette': list(TipoEtichetta.objects.values('id', 'nome', 'quantita')),
        'capsule': list(TipoCapsula.objects.values('id', 'nome', 'quantita')),
        'cestelli': list(TipoCestello.objects.values('id', 'nome', 'quantita')),
    }

    # Silos vino
    silos = list(
        TipologiaVino.objects.select_related('famiglia')
        .values('id', 'nome', 'famiglia__nome', 'quantita_litri')
    )

    # Riepilogo bottiglie
    bottiglie_senza_etichetta = (
        LottoBottiglie.objects.filter(stato=LottoBottiglie.Stato.SENZA_ETICHETTA)
        .aggregate(totale=Sum('quantita'))['totale'] or 0
    )
    bottiglie_complete = (
        LottoBottiglie.objects.filter(stato=LottoBottiglie.Stato.COMPLETA)
        .aggregate(totale=Sum('quantita'))['totale'] or 0
    )

    # Ultimi movimenti
    ultimi_movimenti = MovimentoMagazzinoSerializer(
        MovimentoMagazzino.objects.all()[:10], many=True
    ).data

    return Response({
        'magazzino': magazzino,
        'silos': silos,
        'bottiglie': {
            'senza_etichetta': bottiglie_senza_etichetta,
            'complete': bottiglie_complete,
        },
        'ultimi_movimenti': ultimi_movimenti,
    })


# ─── Riepilogo bottiglie senza etichetta per tipologia ────────────────────

@api_view(['GET'])
def bottiglie_senza_etichetta(request):
    """Ritorna le tipologie con bottiglie in attesa di etichetta e le quantità."""
    from django.db.models import F
    lotti = (
        LottoBottiglie.objects
        .filter(stato=LottoBottiglie.Stato.SENZA_ETICHETTA, ha_etichetta=False)
        .values(
            'tipologia_vino__id',
            'tipologia_vino__nome',
            'tipologia_vino__famiglia__nome',
            'ha_capsula',
        )
        .annotate(totale=Sum('quantita'))
        .order_by('tipologia_vino__famiglia__nome', 'tipologia_vino__nome')
    )
    return Response(list(lotti))
