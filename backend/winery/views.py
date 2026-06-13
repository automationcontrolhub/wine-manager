from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response

from .models import (
    TipoCartone, TipoTappo, TipoBottiglia, TipoEtichetta,
    TipoCapsula, TipoCestello, TipoGadget, FamigliaVino, TipologiaVino,
    LottoBottiglie, MovimentoMagazzino, OperazioneImbottigliamento,
    Cliente, Agente, Ordine, RigaOrdineBottiglia, RigaOrdineGadget,
)
from .serializers import (
    TipoCartoneSerializer, TipoTappoSerializer, TipoBottigliaSerializer,
    TipoEtichettaSerializer, TipoCapsulaSerializer, TipoCestelloSerializer,
    TipoGadgetSerializer,
    FamigliaVinoSerializer, TipologiaVinoSerializer,
    LottoBottiglieSerializer, MovimentoMagazzinoSerializer,
    OperazioneImbottigliamentoSerializer,
    CreaBottiglieSenzaEtichettaSerializer, CreaBottiglieConEtichettaSerializer,
    AssociaEtichettaSerializer, AggiuntaVinoSerializer,
    CaricoMagazzinoSerializer,
    ClienteSerializer, AgenteSerializer,
    OrdineSerializer, OrdineCreateSerializer,
    BottiglieDisponibiliSerializer,
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


class TipoGadgetViewSet(viewsets.ModelViewSet):
    queryset = TipoGadget.objects.all()
    serializer_class = TipoGadgetSerializer
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
        'gadget': (TipoGadget, MovimentoMagazzino.Categoria.GADGET),
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
        'gadget': list(TipoGadget.objects.values('id', 'nome', 'quantita')),
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


# ─── Clienti / Agenti ViewSets ────────────────────────────────────────────

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    pagination_class = None


class AgenteViewSet(viewsets.ModelViewSet):
    queryset = Agente.objects.all()
    serializer_class = AgenteSerializer
    pagination_class = None


# ─── Bottiglie disponibili per la creazione ordine ────────────────────────

@api_view(['GET'])
def bottiglie_disponibili(request):
    """
    Restituisce le bottiglie disponibili per la creazione di un ordine,
    raggruppate per (tipologia_vino, ha_etichetta, ha_capsula).
    Include solo righe con totale > 0.
    """
    lotti = (
        LottoBottiglie.objects
        .values(
            'tipologia_vino__id',
            'tipologia_vino__nome',
            'tipologia_vino__famiglia__nome',
            'ha_etichetta',
            'ha_capsula',
        )
        .annotate(quantita_totale=Sum('quantita'))
        .order_by(
            'tipologia_vino__famiglia__nome', 'tipologia_vino__nome',
            '-ha_etichetta', '-ha_capsula',
        )
    )
    risultato = [
        {
            'tipologia_vino_id': l['tipologia_vino__id'],
            'tipologia_vino_nome': l['tipologia_vino__nome'],
            'famiglia_nome': l['tipologia_vino__famiglia__nome'],
            'ha_etichetta': l['ha_etichetta'],
            'ha_capsula': l['ha_capsula'],
            'quantita_totale': l['quantita_totale'] or 0,
        }
        for l in lotti if (l['quantita_totale'] or 0) > 0
    ]
    return Response(risultato)


# ─── Ordini: helper di scarico / ripristino ───────────────────────────────

def _verifica_disponibilita_ordine(righe_bottiglie, righe_gadget):
    """
    Verifica la disponibilità per un set di righe (bottiglie + gadget).
    Aggrega le richieste per chiave (tipologia, etichetta, capsula) e (gadget_id)
    e confronta con la disponibilità totale in magazzino.
    Ritorna lista errori (vuota se OK).
    """
    errori = []

    # ---- Bottiglie: aggrega per (tipologia_id, ha_etichetta, ha_capsula) -
    richiesta_bott = {}
    for r in righe_bottiglie:
        key = (r['tipologia_vino_id'], bool(r['ha_etichetta']), bool(r['ha_capsula']))
        richiesta_bott[key] = richiesta_bott.get(key, 0) + int(r['quantita'])

    for (tip_id, ha_eti, ha_cap), qty_richiesta in richiesta_bott.items():
        disponibile = (
            LottoBottiglie.objects
            .filter(tipologia_vino_id=tip_id, ha_etichetta=ha_eti, ha_capsula=ha_cap)
            .aggregate(t=Sum('quantita'))['t'] or 0
        )
        if disponibile < qty_richiesta:
            try:
                tip = TipologiaVino.objects.get(id=tip_id)
                nome = str(tip)
            except TipologiaVino.DoesNotExist:
                nome = f"id={tip_id}"
            eti = "etichettate" if ha_eti else "NON etichettate"
            cap = "con capsula" if ha_cap else "senza capsula"
            errori.append(
                f"Bottiglie insufficienti per '{nome}' ({eti}, {cap}): "
                f"richieste {qty_richiesta}, disponibili {disponibile}"
            )

    # ---- Gadget: aggrega per gadget_id ----------------------------------
    richiesta_gad = {}
    for r in righe_gadget:
        gid = r['tipo_gadget_id']
        richiesta_gad[gid] = richiesta_gad.get(gid, 0) + int(r['quantita'])

    for gid, qty_richiesta in richiesta_gad.items():
        try:
            g = TipoGadget.objects.get(id=gid)
        except TipoGadget.DoesNotExist:
            errori.append(f"Gadget id={gid} non trovato")
            continue
        if g.quantita < qty_richiesta:
            errori.append(
                f"Gadget '{g.nome}' insufficiente: richiesti {qty_richiesta}, "
                f"disponibili {g.quantita}"
            )

    return errori


def _scala_bottiglie_per_ordine(tipologia_id, ha_etichetta, ha_capsula, quantita, ordine):
    """
    Scala N bottiglie dai lotti che hanno (tipologia, etichetta, capsula),
    prendendo dai più vecchi (FIFO). Elimina i lotti che si svuotano.
    """
    rimanenti = quantita
    lotti = (
        LottoBottiglie.objects
        .filter(
            tipologia_vino_id=tipologia_id,
            ha_etichetta=ha_etichetta, ha_capsula=ha_capsula,
        )
        .order_by('data_creazione')
    )
    for lotto in lotti:
        if rimanenti <= 0:
            break
        da_prendere = min(rimanenti, lotto.quantita)
        lotto.quantita -= da_prendere
        if lotto.quantita == 0:
            lotto.delete()
        else:
            lotto.save(update_fields=['quantita', 'data_aggiornamento'])
        rimanenti -= da_prendere

    if rimanenti > 0:
        # Sicurezza, non dovrebbe accadere se la verifica è stata fatta
        raise ValueError(f"Disponibilità lotti insufficiente per ordine #{ordine.numero}")

    MovimentoMagazzino.objects.create(
        tipo=MovimentoMagazzino.TipoMovimento.ORDINE_SCARICO,
        categoria=MovimentoMagazzino.Categoria.BOTTIGLIA,
        quantita=quantita,
        descrizione=(
            f"Ordine #{ordine.numero}: scarico {quantita} bott. tipologia id={tipologia_id} "
            f"(eti={ha_etichetta}, cap={ha_capsula})"
        ),
        riferimento_id=ordine.id,
        riferimento_tipo='Ordine',
    )


def _ripristina_bottiglie_da_ordine(tipologia, ha_etichetta, ha_capsula, quantita, ordine):
    """
    Rimette nel lotto corrispondente (o ne crea uno nuovo) N bottiglie.
    """
    stato = (
        LottoBottiglie.Stato.COMPLETA if ha_etichetta
        else LottoBottiglie.Stato.SENZA_ETICHETTA
    )
    lotto = LottoBottiglie.objects.filter(
        tipologia_vino=tipologia,
        ha_etichetta=ha_etichetta,
        ha_capsula=ha_capsula,
        stato=stato,
    ).first()
    if lotto:
        lotto.quantita += quantita
        lotto.save(update_fields=['quantita', 'data_aggiornamento'])
    else:
        LottoBottiglie.objects.create(
            tipologia_vino=tipologia,
            quantita=quantita,
            stato=stato,
            ha_etichetta=ha_etichetta,
            ha_capsula=ha_capsula,
        )

    MovimentoMagazzino.objects.create(
        tipo=MovimentoMagazzino.TipoMovimento.ORDINE_RIPRISTINO,
        categoria=MovimentoMagazzino.Categoria.BOTTIGLIA,
        quantita=quantita,
        descrizione=(
            f"Annullamento ordine #{ordine.numero}: ripristino {quantita} bott. {tipologia} "
            f"(eti={ha_etichetta}, cap={ha_capsula})"
        ),
        riferimento_id=ordine.id,
        riferimento_tipo='Ordine',
    )


def _scala_gadget_per_ordine(tipo_gadget, quantita, ordine):
    tipo_gadget.quantita -= quantita
    tipo_gadget.save(update_fields=['quantita'])
    MovimentoMagazzino.objects.create(
        tipo=MovimentoMagazzino.TipoMovimento.ORDINE_SCARICO,
        categoria=MovimentoMagazzino.Categoria.GADGET,
        quantita=quantita,
        descrizione=f"Ordine #{ordine.numero}: scarico {quantita}× gadget '{tipo_gadget.nome}'",
        riferimento_id=ordine.id,
        riferimento_tipo='Ordine',
    )


def _ripristina_gadget_da_ordine(tipo_gadget, quantita, ordine):
    tipo_gadget.quantita += quantita
    tipo_gadget.save(update_fields=['quantita'])
    MovimentoMagazzino.objects.create(
        tipo=MovimentoMagazzino.TipoMovimento.ORDINE_RIPRISTINO,
        categoria=MovimentoMagazzino.Categoria.GADGET,
        quantita=quantita,
        descrizione=f"Annullamento ordine #{ordine.numero}: ripristino {quantita}× gadget '{tipo_gadget.nome}'",
        riferimento_id=ordine.id,
        riferimento_tipo='Ordine',
    )


def _applica_scarico_ordine(ordine):
    """Per ogni riga dell'ordine, scala le quantità dal magazzino."""
    for r in ordine.righe_bottiglie.all():
        _scala_bottiglie_per_ordine(
            r.tipologia_vino_id, r.ha_etichetta, r.ha_capsula, r.quantita, ordine
        )
    for r in ordine.righe_gadget.select_related('tipo_gadget').all():
        _scala_gadget_per_ordine(r.tipo_gadget, r.quantita, ordine)


def _applica_ripristino_ordine(ordine):
    """Per ogni riga dell'ordine, rimette in magazzino."""
    for r in ordine.righe_bottiglie.select_related('tipologia_vino').all():
        _ripristina_bottiglie_da_ordine(
            r.tipologia_vino, r.ha_etichetta, r.ha_capsula, r.quantita, ordine
        )
    for r in ordine.righe_gadget.select_related('tipo_gadget').all():
        _ripristina_gadget_da_ordine(r.tipo_gadget, r.quantita, ordine)


# ─── Ordini ViewSet ───────────────────────────────────────────────────────

class OrdineViewSet(viewsets.ModelViewSet):
    """
    CRUD ordini:
    - list / retrieve: serializzazione completa con righe e totali
    - create: richiede righe_bottiglie + righe_gadget, scala magazzino
    - partial_update (PATCH): aggiorna campi (sconto, IVA, tracking, flag, agente, note);
        se sono passate righe_bottiglie / righe_gadget, ricostruisce le righe ripristinando
        il magazzino e riscalando le nuove (solo se l'ordine è CONFERMATO).
    - destroy: elimina l'ordine; se CONFERMATO ripristina il magazzino.
    - POST /api/ordini/{id}/annulla/: ANNULLA l'ordine e ripristina magazzino.
    - POST /api/ordini/{id}/ripristina/: riporta CONFERMATO un ordine ANNULLATO (riscalando).
    """
    queryset = Ordine.objects.select_related('cliente', 'agente').prefetch_related(
        'righe_bottiglie__tipologia_vino__famiglia',
        'righe_gadget__tipo_gadget',
    ).all()
    serializer_class = OrdineSerializer
    filterset_fields = ['stato', 'cliente', 'agente', 'pacco_arrivato', 'fattura_pagata']

    # ---- Create -----------------------------------------------------------

    def create(self, request, *args, **kwargs):
        ser = OrdineCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data

        # Verifica cliente / agente
        try:
            cliente = Cliente.objects.get(id=d['cliente_id'])
        except Cliente.DoesNotExist:
            return Response({'error': 'Cliente non trovato'}, status=404)

        agente = None
        if d.get('agente_id'):
            try:
                agente = Agente.objects.get(id=d['agente_id'])
            except Agente.DoesNotExist:
                return Response({'error': 'Agente non trovato'}, status=404)

        # Verifica disponibilità magazzino
        errori = _verifica_disponibilita_ordine(d['righe_bottiglie'], d.get('righe_gadget') or [])
        if errori:
            return Response({'errors': errori}, status=400)

        with transaction.atomic():
            ordine = Ordine.objects.create(
                cliente=cliente,
                agente=agente,
                sconto_percentuale=d.get('sconto_percentuale') or Decimal('0'),
                aliquota_iva=d.get('aliquota_iva') or Decimal('22'),
                tracking_number=d.get('tracking_number') or '',
                pacco_arrivato=d.get('pacco_arrivato') or False,
                fattura_pagata=d.get('fattura_pagata') or False,
                stato=Ordine.Stato.CONFERMATO,
                note=d.get('note') or '',
            )

            for r in d['righe_bottiglie']:
                RigaOrdineBottiglia.objects.create(
                    ordine=ordine,
                    tipologia_vino_id=r['tipologia_vino_id'],
                    ha_etichetta=r['ha_etichetta'],
                    ha_capsula=r['ha_capsula'],
                    quantita=r['quantita'],
                    prezzo_unitario=r['prezzo_unitario'],
                )

            for r in (d.get('righe_gadget') or []):
                RigaOrdineGadget.objects.create(
                    ordine=ordine,
                    tipo_gadget_id=r['tipo_gadget_id'],
                    quantita=r['quantita'],
                )

            _applica_scarico_ordine(ordine)

        ordine.refresh_from_db()
        return Response(OrdineSerializer(ordine).data, status=201)

    # ---- Update -----------------------------------------------------------

    def update(self, request, *args, **kwargs):
        # PUT non supportato: usare PATCH (partial_update)
        return self.partial_update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """
        Aggiorna l'ordine.

        - Campi semplici (sconto, IVA, tracking, flag, agente, note): sempre modificabili.
        - 'cliente_id': modificabile (ricollega).
        - Se vengono passate 'righe_bottiglie' o 'righe_gadget' e l'ordine è CONFERMATO,
          ricostruisce le righe ripristinando il magazzino e riscalando le nuove.
          Se è ANNULLATO, modifica solo le righe in tabella (senza toccare il magazzino).
        """
        ordine = self.get_object()
        data = request.data
        ricostruisci_righe = 'righe_bottiglie' in data or 'righe_gadget' in data

        with transaction.atomic():
            # ---- Campi semplici ---------------------------------------
            if 'cliente_id' in data and data['cliente_id'] is not None:
                try:
                    ordine.cliente = Cliente.objects.get(id=data['cliente_id'])
                except Cliente.DoesNotExist:
                    return Response({'error': 'Cliente non trovato'}, status=404)

            if 'agente_id' in data:
                if data['agente_id'] in (None, ''):
                    ordine.agente = None
                else:
                    try:
                        ordine.agente = Agente.objects.get(id=data['agente_id'])
                    except Agente.DoesNotExist:
                        return Response({'error': 'Agente non trovato'}, status=404)

            for campo in ['sconto_percentuale', 'aliquota_iva', 'tracking_number',
                          'pacco_arrivato', 'fattura_pagata', 'note']:
                if campo in data:
                    setattr(ordine, campo, data[campo])

            # ---- Ricostruzione righe ----------------------------------
            if ricostruisci_righe:
                nuove_bott = data.get(
                    'righe_bottiglie',
                    list(ordine.righe_bottiglie.values(
                        'tipologia_vino_id', 'ha_etichetta', 'ha_capsula',
                        'quantita', 'prezzo_unitario',
                    ))
                )
                nuove_gad = data.get(
                    'righe_gadget',
                    list(ordine.righe_gadget.values('tipo_gadget_id', 'quantita'))
                )

                # Normalizza tipi
                nuove_bott_norm = []
                for r in nuove_bott:
                    nuove_bott_norm.append({
                        'tipologia_vino_id': int(r.get('tipologia_vino_id') or r.get('tipologia_vino')),
                        'ha_etichetta': bool(r.get('ha_etichetta', True)),
                        'ha_capsula': bool(r.get('ha_capsula', True)),
                        'quantita': int(r['quantita']),
                        'prezzo_unitario': Decimal(str(r['prezzo_unitario'])),
                    })
                nuove_gad_norm = []
                for r in nuove_gad:
                    nuove_gad_norm.append({
                        'tipo_gadget_id': int(r.get('tipo_gadget_id') or r.get('tipo_gadget')),
                        'quantita': int(r['quantita']),
                    })

                if not nuove_bott_norm:
                    return Response(
                        {'error': "L'ordine deve contenere almeno una bottiglia."},
                        status=400,
                    )

                if ordine.stato == Ordine.Stato.CONFERMATO:
                    # Calcola DELTA per evitare di toccare temporaneamente il magazzino:
                    # disponibilità_effettiva = giacenza_attuale + scarico_originale - nuovo_scarico
                    # Per semplicità: ripristina vecchio, verifica e scala nuovo.
                    # Per evitare race, facciamo tutto in transazione.
                    _applica_ripristino_ordine(ordine)

                    # Elimina righe vecchie
                    ordine.righe_bottiglie.all().delete()
                    ordine.righe_gadget.all().delete()

                    # Verifica disponibilità per le nuove
                    errori = _verifica_disponibilita_ordine(nuove_bott_norm, nuove_gad_norm)
                    if errori:
                        # Rollback automatico via transaction
                        from rest_framework.exceptions import ValidationError
                        raise ValidationError({'errors': errori})

                    # Crea nuove righe e scala
                    for r in nuove_bott_norm:
                        RigaOrdineBottiglia.objects.create(
                            ordine=ordine,
                            tipologia_vino_id=r['tipologia_vino_id'],
                            ha_etichetta=r['ha_etichetta'],
                            ha_capsula=r['ha_capsula'],
                            quantita=r['quantita'],
                            prezzo_unitario=r['prezzo_unitario'],
                        )
                    for r in nuove_gad_norm:
                        RigaOrdineGadget.objects.create(
                            ordine=ordine,
                            tipo_gadget_id=r['tipo_gadget_id'],
                            quantita=r['quantita'],
                        )
                    _applica_scarico_ordine(ordine)
                else:
                    # ANNULLATO: aggiorna solo i dati senza toccare il magazzino
                    ordine.righe_bottiglie.all().delete()
                    ordine.righe_gadget.all().delete()
                    for r in nuove_bott_norm:
                        RigaOrdineBottiglia.objects.create(
                            ordine=ordine,
                            tipologia_vino_id=r['tipologia_vino_id'],
                            ha_etichetta=r['ha_etichetta'],
                            ha_capsula=r['ha_capsula'],
                            quantita=r['quantita'],
                            prezzo_unitario=r['prezzo_unitario'],
                        )
                    for r in nuove_gad_norm:
                        RigaOrdineGadget.objects.create(
                            ordine=ordine,
                            tipo_gadget_id=r['tipo_gadget_id'],
                            quantita=r['quantita'],
                        )

            ordine.save()

        ordine.refresh_from_db()
        return Response(OrdineSerializer(ordine).data)

    # ---- Destroy ---------------------------------------------------------

    def destroy(self, request, *args, **kwargs):
        """
        Eliminazione fisica dell'ordine. Se è CONFERMATO ripristina il magazzino.
        """
        ordine = self.get_object()
        with transaction.atomic():
            if ordine.stato == Ordine.Stato.CONFERMATO:
                _applica_ripristino_ordine(ordine)
            ordine.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ---- Annulla / Ripristina --------------------------------------------

    @action(detail=True, methods=['post'])
    def annulla(self, request, pk=None):
        """Annulla l'ordine: stato → ANNULLATO e ripristina il magazzino."""
        ordine = self.get_object()
        if ordine.stato == Ordine.Stato.ANNULLATO:
            return Response({'error': 'Ordine già annullato'}, status=400)

        with transaction.atomic():
            _applica_ripristino_ordine(ordine)
            ordine.stato = Ordine.Stato.ANNULLATO
            ordine.data_annullamento = timezone.now()
            ordine.save(update_fields=['stato', 'data_annullamento'])

        ordine.refresh_from_db()
        return Response(OrdineSerializer(ordine).data)

    @action(detail=True, methods=['post'])
    def ripristina(self, request, pk=None):
        """Riporta un ordine ANNULLATO a CONFERMATO, riscalando il magazzino."""
        ordine = self.get_object()
        if ordine.stato == Ordine.Stato.CONFERMATO:
            return Response({'error': 'Ordine già confermato'}, status=400)

        # Verifica disponibilità con le righe attuali
        righe_bott = list(ordine.righe_bottiglie.values(
            'tipologia_vino_id', 'ha_etichetta', 'ha_capsula', 'quantita'
        ))
        righe_bott_for_check = [
            {
                'tipologia_vino_id': r['tipologia_vino_id'],
                'ha_etichetta': r['ha_etichetta'],
                'ha_capsula': r['ha_capsula'],
                'quantita': r['quantita'],
            } for r in righe_bott
        ]
        righe_gad = list(ordine.righe_gadget.values('tipo_gadget_id', 'quantita'))
        errori = _verifica_disponibilita_ordine(righe_bott_for_check, righe_gad)
        if errori:
            return Response({'errors': errori}, status=400)

        with transaction.atomic():
            _applica_scarico_ordine(ordine)
            ordine.stato = Ordine.Stato.CONFERMATO
            ordine.data_annullamento = None
            ordine.save(update_fields=['stato', 'data_annullamento'])

        ordine.refresh_from_db()
        return Response(OrdineSerializer(ordine).data)

