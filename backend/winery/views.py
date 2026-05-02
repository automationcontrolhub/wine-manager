from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response

from .models import (
    TipoCartone, TipoTappo, TipoBottiglia, TipoEtichetta,
    TipoCapsula, TipoCestello, FamigliaVino, TipologiaVino,
    LottoBottiglie, MovimentoMagazzino, OperazioneImbottigliamento,
)
from .serializers import (
    TipoCartoneSerializer, TipoTappoSerializer, TipoBottigliaSerializer,
    TipoEtichettaSerializer, TipoCapsulaSerializer, TipoCestelloSerializer,
    FamigliaVinoSerializer, TipologiaVinoSerializer,
    LottoBottiglieSerializer, MovimentoMagazzinoSerializer,
    OperazioneImbottigliamentoSerializer,
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

        # Salva snapshot operazione per annullamento
        OperazioneImbottigliamento.objects.create(
            tipo=OperazioneImbottigliamento.TipoOperazione.CREA_SENZA_ETICHETTA,
            tipologia_vino=tipologia,
            quantita=quantita,
            con_etichetta=False,
            con_capsula=con_capsula,
            dettagli={'lotto_id': lotto.id},
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

        # Salva snapshot operazione per annullamento
        OperazioneImbottigliamento.objects.create(
            tipo=OperazioneImbottigliamento.TipoOperazione.CREA_CON_ETICHETTA,
            tipologia_vino=tipologia,
            quantita=quantita,
            con_etichetta=True,
            con_capsula=con_capsula,
            dettagli={'lotto_id': lotto.id},
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

        # Salva snapshot operazione per annullamento
        # Memorizziamo i dettagli dei lotti origine consumati per poter ripristinare
        lotti_consumati_dettagli = []
        rimanenti = quantita
        # Riprendiamo l'ordinamento corretto dei lotti origine
        if con_capsula:
            lotti_check = LottoBottiglie.objects.filter(
                tipologia_vino=tipologia_origine,
                stato=LottoBottiglie.Stato.SENZA_ETICHETTA,
                ha_etichetta=False,
            ).order_by('ha_capsula', 'data_creazione')
        else:
            lotti_check = LottoBottiglie.objects.filter(
                tipologia_vino=tipologia_origine,
                stato=LottoBottiglie.Stato.SENZA_ETICHETTA,
                ha_etichetta=False,
            ).order_by('-ha_capsula', 'data_creazione')

        # Nota: a questo punto i lotti sono già stati scalati, quindi salviamo
        # solo i totali per ricostruire in caso di annullamento
        OperazioneImbottigliamento.objects.create(
            tipo=OperazioneImbottigliamento.TipoOperazione.ASSOCIA_ETICHETTA,
            tipologia_vino=tipologia_origine,
            tipologia_vino_destinazione=tipologia_dest,
            quantita=quantita,
            con_etichetta=True,
            con_capsula=con_capsula,
            dettagli={
                'lotto_dest_id': lotto_completo.id,
                'capsule_aggiunte': capsule_da_aggiungere,
                'tipologia_origine_id': tipologia_origine.id,
                'tipologia_dest_id': tipologia_dest.id,
            },
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


# ─── Operazioni: lista e annullamento ─────────────────────────────────────

class OperazioneImbottigliamentoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OperazioneImbottigliamento.objects.select_related(
        'tipologia_vino', 'tipologia_vino__famiglia',
        'tipologia_vino_destinazione', 'tipologia_vino_destinazione__famiglia',
    ).all()
    serializer_class = OperazioneImbottigliamentoSerializer
    filterset_fields = ['stato', 'tipo']


@api_view(['POST'])
def annulla_operazione(request, pk):
    """
    Annulla una operazione di imbottigliamento ripristinando lo stato precedente:
    - Materiali tornano in magazzino
    - Vino torna nel silos (per crea_*)
    - Lotti bottiglie tornano allo stato precedente
    
    NB: per ASSOCIA_ETICHETTA non si può ricostruire l'esatta distribuzione
    dei lotti origine (con/senza capsula), quindi si crea un lotto unificato
    con lo stato corrispondente al flag con_capsula dell'operazione.
    """
    try:
        op = OperazioneImbottigliamento.objects.select_related(
            'tipologia_vino', 'tipologia_vino__famiglia',
            'tipologia_vino__tipo_cartone', 'tipologia_vino__tipo_tappo',
            'tipologia_vino__tipo_bottiglia', 'tipologia_vino__tipo_etichetta',
            'tipologia_vino__tipo_capsula', 'tipologia_vino__tipo_cestello',
            'tipologia_vino_destinazione', 'tipologia_vino_destinazione__famiglia',
            'tipologia_vino_destinazione__tipo_etichetta',
            'tipologia_vino_destinazione__tipo_capsula',
        ).get(pk=pk)
    except OperazioneImbottigliamento.DoesNotExist:
        return Response({'error': 'Operazione non trovata'}, status=404)

    if op.stato == OperazioneImbottigliamento.Stato.ANNULLATA:
        return Response({'error': 'Operazione già annullata'}, status=400)

    with transaction.atomic():
        if op.tipo == OperazioneImbottigliamento.TipoOperazione.CREA_SENZA_ETICHETTA:
            _annulla_crea_senza_etichetta(op)
        elif op.tipo == OperazioneImbottigliamento.TipoOperazione.CREA_CON_ETICHETTA:
            _annulla_crea_con_etichetta(op)
        elif op.tipo == OperazioneImbottigliamento.TipoOperazione.ASSOCIA_ETICHETTA:
            errore = _annulla_associa_etichetta(op)
            if errore:
                # Solleva eccezione per fare rollback
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'errors': [errore]})

        op.stato = OperazioneImbottigliamento.Stato.ANNULLATA
        op.data_annullamento = timezone.now()
        op.save(update_fields=['stato', 'data_annullamento'])

        MovimentoMagazzino.objects.create(
            tipo=MovimentoMagazzino.TipoMovimento.ANNULLAMENTO,
            categoria=MovimentoMagazzino.Categoria.BOTTIGLIA,
            quantita=op.quantita,
            descrizione=f"Annullata operazione: {op.get_tipo_display()} × {op.quantita} ({op.tipologia_vino})",
        )

    return Response(OperazioneImbottigliamentoSerializer(op).data)


def _annulla_crea_senza_etichetta(op):
    """Annulla creazione senza etichetta: ripristina materiali e rimuove dal lotto."""
    tipologia = op.tipologia_vino
    quantita = op.quantita
    con_capsula = op.con_capsula

    # Ripristina materiali in magazzino
    _ripristina_materiali(tipologia, quantita, con_etichetta=False, con_capsula=con_capsula)

    # Sottrai dal lotto senza etichetta
    lotto = LottoBottiglie.objects.filter(
        tipologia_vino=tipologia,
        stato=LottoBottiglie.Stato.SENZA_ETICHETTA,
        ha_etichetta=False,
        ha_capsula=con_capsula,
    ).first()

    if lotto:
        if lotto.quantita > quantita:
            lotto.quantita -= quantita
            lotto.save(update_fields=['quantita', 'data_aggiornamento'])
        elif lotto.quantita == quantita:
            lotto.delete()
        else:
            # Se ci sono meno bottiglie nel lotto di quanto annullare, eliminiamo solo quello che c'è
            lotto.delete()


def _annulla_crea_con_etichetta(op):
    """Annulla creazione con etichetta: ripristina materiali e rimuove dal lotto completo."""
    tipologia = op.tipologia_vino
    quantita = op.quantita
    con_capsula = op.con_capsula

    # Ripristina materiali in magazzino
    _ripristina_materiali(tipologia, quantita, con_etichetta=True, con_capsula=con_capsula)

    # Sottrai dal lotto completo
    lotto = LottoBottiglie.objects.filter(
        tipologia_vino=tipologia,
        stato=LottoBottiglie.Stato.COMPLETA,
        ha_etichetta=True,
        ha_capsula=con_capsula,
    ).first()

    if lotto:
        if lotto.quantita > quantita:
            lotto.quantita -= quantita
            lotto.save(update_fields=['quantita', 'data_aggiornamento'])
        else:
            lotto.delete()


def _annulla_associa_etichetta(op):
    """
    Annulla associa etichetta: 
    - Rimette etichette (e capsule se aggiunte) in magazzino
    - Sottrae dal lotto destinazione
    - Riporta le bottiglie come "senza etichetta" della tipologia origine
    """
    tipologia_origine = op.tipologia_vino
    tipologia_dest = op.tipologia_vino_destinazione
    quantita = op.quantita
    con_capsula = op.con_capsula
    capsule_aggiunte = op.dettagli.get('capsule_aggiunte', 0)

    # Verifica che ci siano abbastanza bottiglie nel lotto destinazione
    lotto_dest = LottoBottiglie.objects.filter(
        tipologia_vino=tipologia_dest,
        stato=LottoBottiglie.Stato.COMPLETA,
        ha_etichetta=True,
        ha_capsula=con_capsula,
    ).first()

    disponibili = lotto_dest.quantita if lotto_dest else 0
    if disponibili < quantita:
        return (
            f"Impossibile annullare: il lotto di destinazione ha solo {disponibili} "
            f"bottiglie ({tipologia_dest}), ne servono {quantita}. "
            "Le bottiglie potrebbero essere state spostate o vendute."
        )

    # Ripristina etichette in magazzino
    tipologia_dest.tipo_etichetta.quantita += quantita
    tipologia_dest.tipo_etichetta.save(update_fields=['quantita'])
    MovimentoMagazzino.objects.create(
        tipo=MovimentoMagazzino.TipoMovimento.ANNULLAMENTO,
        categoria=MovimentoMagazzino.Categoria.ETICHETTA,
        quantita=quantita,
        descrizione=f"Annullamento associa etichetta: ripristino {quantita} etichette '{tipologia_dest.tipo_etichetta.nome}'",
    )

    # Ripristina capsule se erano state aggiunte
    if capsule_aggiunte > 0:
        tipologia_dest.tipo_capsula.quantita += capsule_aggiunte
        tipologia_dest.tipo_capsula.save(update_fields=['quantita'])
        MovimentoMagazzino.objects.create(
            tipo=MovimentoMagazzino.TipoMovimento.ANNULLAMENTO,
            categoria=MovimentoMagazzino.Categoria.CAPSULA,
            quantita=capsule_aggiunte,
            descrizione=f"Annullamento associa etichetta: ripristino {capsule_aggiunte} capsule",
        )

    # Sottrai dal lotto destinazione
    if lotto_dest.quantita > quantita:
        lotto_dest.quantita -= quantita
        lotto_dest.save(update_fields=['quantita', 'data_aggiornamento'])
    else:
        lotto_dest.delete()

    # Rimetti come bottiglie senza etichetta della ORIGINE
    # Stato capsula: se nello step originale era stato attivato il flag, le bottiglie 
    # ora hanno la capsula. Altrimenti seguono lo stato originale.
    # Per semplicità, se capsule erano state aggiunte, mettiamo bottiglie con capsula
    # nelle bottiglie senza etichetta. Per il resto, senza capsula.
    bottiglie_con_capsula_da_ripristinare = quantita - capsule_aggiunte
    bottiglie_senza_capsula_da_ripristinare = capsule_aggiunte if con_capsula else (quantita if not con_capsula else 0)
    
    # In realtà, per essere coerenti:
    # - se con_capsula=True: alcune avevano capsula (quantita - capsule_aggiunte) altre no (capsule_aggiunte)
    #   ma ora tutte hanno capsula, quindi rimetto tutte CON capsula? No, ripristino lo stato precedente.
    #   capsule_aggiunte = quante NON avevano capsula prima
    #   quindi: senza capsula = capsule_aggiunte, con capsula = quantita - capsule_aggiunte
    # - se con_capsula=False: nessuna capsula aggiunta, quindi rimangono come prima
    #   tutte avevano lo stato originale che però non sappiamo... assumiamo tutte CON (più probabile)
    
    if con_capsula:
        senza_cap = capsule_aggiunte
        con_cap = quantita - capsule_aggiunte
    else:
        # Caso "senza capsula" nel form: prendevamo prima quelle CON capsula
        # quindi quelle ripristinate erano con capsula
        senza_cap = 0
        con_cap = quantita

    # Crea lotto senza etichetta CON capsula (se applicabile)
    if con_cap > 0:
        lotto_con = LottoBottiglie.objects.filter(
            tipologia_vino=tipologia_origine,
            stato=LottoBottiglie.Stato.SENZA_ETICHETTA,
            ha_etichetta=False,
            ha_capsula=True,
        ).first()
        if lotto_con:
            lotto_con.quantita += con_cap
            lotto_con.save(update_fields=['quantita', 'data_aggiornamento'])
        else:
            LottoBottiglie.objects.create(
                tipologia_vino=tipologia_origine,
                quantita=con_cap,
                stato=LottoBottiglie.Stato.SENZA_ETICHETTA,
                ha_etichetta=False,
                ha_capsula=True,
            )

    # Crea lotto senza etichetta SENZA capsula (se applicabile)
    if senza_cap > 0:
        lotto_sc = LottoBottiglie.objects.filter(
            tipologia_vino=tipologia_origine,
            stato=LottoBottiglie.Stato.SENZA_ETICHETTA,
            ha_etichetta=False,
            ha_capsula=False,
        ).first()
        if lotto_sc:
            lotto_sc.quantita += senza_cap
            lotto_sc.save(update_fields=['quantita', 'data_aggiornamento'])
        else:
            LottoBottiglie.objects.create(
                tipologia_vino=tipologia_origine,
                quantita=senza_cap,
                stato=LottoBottiglie.Stato.SENZA_ETICHETTA,
                ha_etichetta=False,
                ha_capsula=False,
            )

    return None  # nessun errore


def _ripristina_materiali(tipologia, quantita, con_etichetta=True, con_capsula=True):
    """Rimette materiali in magazzino e vino nel silos (inverso di _scala_materiali)."""
    is_spumante = tipologia.famiglia.is_spumante
    capacita_bottiglia = tipologia.tipo_bottiglia.capacita_litri
    litri = Decimal(str(quantita)) * capacita_bottiglia
    cap = tipologia.tipo_cartone.capacita_bottiglie
    cartoni = -(-quantita // cap)

    # Ripristina vino
    tipologia.quantita_litri += litri
    tipologia.save(update_fields=['quantita_litri'])
    MovimentoMagazzino.objects.create(
        tipo=MovimentoMagazzino.TipoMovimento.ANNULLAMENTO,
        categoria=MovimentoMagazzino.Categoria.VINO,
        quantita=litri,
        descrizione=f"Ripristino {litri}L per annullamento ({tipologia})",
    )

    # Ripristina bottiglie
    tipologia.tipo_bottiglia.quantita += quantita
    tipologia.tipo_bottiglia.save(update_fields=['quantita'])
    MovimentoMagazzino.objects.create(
        tipo=MovimentoMagazzino.TipoMovimento.ANNULLAMENTO,
        categoria=MovimentoMagazzino.Categoria.BOTTIGLIA,
        quantita=quantita,
        descrizione=f"Ripristino {quantita} bottiglie '{tipologia.tipo_bottiglia.nome}'",
    )

    # Ripristina tappi
    tipologia.tipo_tappo.quantita += quantita
    tipologia.tipo_tappo.save(update_fields=['quantita'])
    MovimentoMagazzino.objects.create(
        tipo=MovimentoMagazzino.TipoMovimento.ANNULLAMENTO,
        categoria=MovimentoMagazzino.Categoria.TAPPO,
        quantita=quantita,
        descrizione=f"Ripristino {quantita} tappi '{tipologia.tipo_tappo.nome}'",
    )

    # Ripristina etichette
    if con_etichetta:
        tipologia.tipo_etichetta.quantita += quantita
        tipologia.tipo_etichetta.save(update_fields=['quantita'])
        MovimentoMagazzino.objects.create(
            tipo=MovimentoMagazzino.TipoMovimento.ANNULLAMENTO,
            categoria=MovimentoMagazzino.Categoria.ETICHETTA,
            quantita=quantita,
            descrizione=f"Ripristino {quantita} etichette '{tipologia.tipo_etichetta.nome}'",
        )

    # Ripristina capsule
    if con_capsula:
        tipologia.tipo_capsula.quantita += quantita
        tipologia.tipo_capsula.save(update_fields=['quantita'])
        MovimentoMagazzino.objects.create(
            tipo=MovimentoMagazzino.TipoMovimento.ANNULLAMENTO,
            categoria=MovimentoMagazzino.Categoria.CAPSULA,
            quantita=quantita,
            descrizione=f"Ripristino {quantita} capsule '{tipologia.tipo_capsula.nome}'",
        )

    # Ripristina cestelli
    if is_spumante and tipologia.tipo_cestello:
        tipologia.tipo_cestello.quantita += quantita
        tipologia.tipo_cestello.save(update_fields=['quantita'])
        MovimentoMagazzino.objects.create(
            tipo=MovimentoMagazzino.TipoMovimento.ANNULLAMENTO,
            categoria=MovimentoMagazzino.Categoria.CESTELLO,
            quantita=quantita,
            descrizione=f"Ripristino {quantita} cestelli",
        )

    # Ripristina cartoni
    tipologia.tipo_cartone.quantita += cartoni
    tipologia.tipo_cartone.save(update_fields=['quantita'])
    MovimentoMagazzino.objects.create(
        tipo=MovimentoMagazzino.TipoMovimento.ANNULLAMENTO,
        categoria=MovimentoMagazzino.Categoria.CARTONE,
        quantita=cartoni,
        descrizione=f"Ripristino {cartoni} cartoni '{tipologia.tipo_cartone.nome}'",
    )
