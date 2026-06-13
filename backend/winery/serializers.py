from rest_framework import serializers
from decimal import Decimal
from .models import (
    TipoCartone, TipoTappo, TipoBottiglia, TipoEtichetta,
    TipoCapsula, TipoCestello, TipoGadget, FamigliaVino, TipologiaVino,
    LottoBottiglie, MovimentoMagazzino, OperazioneImbottigliamento,
    Cliente, Agente, Ordine, RigaOrdineBottiglia, RigaOrdineGadget,
)


# ─── Materiali ────────────────────────────────────────────────────────────

class TipoCartoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoCartone
        fields = '__all__'


class TipoTappoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoTappo
        fields = '__all__'


class TipoBottigliaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoBottiglia
        fields = '__all__'


class TipoEtichettaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoEtichetta
        fields = '__all__'


class TipoCapsulaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoCapsula
        fields = '__all__'


class TipoCestelloSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoCestello
        fields = '__all__'


class TipoGadgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoGadget
        fields = '__all__'


# ─── Vino ─────────────────────────────────────────────────────────────────

class FamigliaVinoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamigliaVino
        fields = '__all__'


class TipologiaVinoSerializer(serializers.ModelSerializer):
    famiglia_nome = serializers.CharField(source='famiglia.nome', read_only=True)
    famiglia_is_spumante = serializers.BooleanField(source='famiglia.is_spumante', read_only=True)
    tipo_cartone_nome = serializers.CharField(source='tipo_cartone.nome', read_only=True)
    tipo_cartone_capacita = serializers.IntegerField(
        source='tipo_cartone.capacita_bottiglie', read_only=True
    )
    tipo_tappo_nome = serializers.CharField(source='tipo_tappo.nome', read_only=True)
    tipo_bottiglia_nome = serializers.CharField(source='tipo_bottiglia.nome', read_only=True)
    tipo_bottiglia_capacita = serializers.DecimalField(
        source='tipo_bottiglia.capacita_litri', read_only=True,
        max_digits=5, decimal_places=2
    )
    tipo_etichetta_nome = serializers.CharField(source='tipo_etichetta.nome', read_only=True)
    tipo_capsula_nome = serializers.CharField(source='tipo_capsula.nome', read_only=True)
    tipo_cestello_nome = serializers.CharField(source='tipo_cestello.nome', read_only=True, allow_null=True)

    class Meta:
        model = TipologiaVino
        fields = '__all__'


class AggiuntaVinoSerializer(serializers.Serializer):
    """Per aggiungere litri a un silos esistente."""
    tipologia_vino_id = serializers.IntegerField()
    litri = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))


# ─── Lotti ────────────────────────────────────────────────────────────────

class LottoBottiglieSerializer(serializers.ModelSerializer):
    tipologia_vino_nome = serializers.CharField(source='tipologia_vino.__str__', read_only=True)
    famiglia_nome = serializers.CharField(source='tipologia_vino.famiglia.nome', read_only=True)

    class Meta:
        model = LottoBottiglie
        fields = '__all__'


class CreaBottiglieSenzaEtichettaSerializer(serializers.Serializer):
    """Step 1: crea bottiglie senza etichetta."""
    tipologia_vino_id = serializers.IntegerField()
    quantita = serializers.IntegerField(min_value=1)
    con_capsula = serializers.BooleanField(default=False)


class CreaBottiglieConEtichettaSerializer(serializers.Serializer):
    """Creazione diretta con etichetta."""
    tipologia_vino_id = serializers.IntegerField()
    quantita = serializers.IntegerField(min_value=1)
    con_capsula = serializers.BooleanField(default=True)


class AssociaEtichettaSerializer(serializers.Serializer):
    """Associa etichetta a bottiglie senza etichetta esistenti."""
    tipologia_vino_origine_id = serializers.IntegerField(
        help_text="ID della tipologia di vino delle bottiglie senza etichetta da prendere"
    )
    tipologia_vino_destinazione_id = serializers.IntegerField(
        help_text="ID della tipologia di vino con cui etichettare (può essere diversa dall'origine)"
    )
    quantita = serializers.IntegerField(min_value=1)
    con_capsula = serializers.BooleanField(
        default=False,
        help_text="Se True e la capsula non era stata inserita nello step precedente"
    )


# ─── Movimenti ────────────────────────────────────────────────────────────

class MovimentoMagazzinoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovimentoMagazzino
        fields = '__all__'


# ─── Carico magazzino ─────────────────────────────────────────────────────

class CaricoMagazzinoSerializer(serializers.Serializer):
    """Per fare un carico di materiale in magazzino."""
    categoria = serializers.ChoiceField(choices=[
        'cartone', 'tappo', 'bottiglia', 'etichetta', 'capsula', 'cestello', 'gadget'
    ])
    tipo_id = serializers.IntegerField()
    quantita = serializers.IntegerField(min_value=1)


class OperazioneImbottigliamentoSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    stato_display = serializers.CharField(source='get_stato_display', read_only=True)
    tipologia_vino_nome = serializers.SerializerMethodField()
    tipologia_vino_destinazione_nome = serializers.SerializerMethodField()

    def get_tipologia_vino_nome(self, obj):
        return str(obj.tipologia_vino) if obj.tipologia_vino else None

    def get_tipologia_vino_destinazione_nome(self, obj):
        return str(obj.tipologia_vino_destinazione) if obj.tipologia_vino_destinazione else None

    class Meta:
        model = OperazioneImbottigliamento
        fields = '__all__'


# ─── Rettifica ────────────────────────────────────────────────────────────

class RettificaMagazzinoSerializer(serializers.Serializer):
    """Per impostare la quantità assoluta di un materiale in magazzino con logging."""
    categoria = serializers.ChoiceField(choices=[
        'cartone', 'tappo', 'bottiglia', 'etichetta', 'capsula', 'cestello', 'gadget'
    ])
    tipo_id = serializers.IntegerField()
    nuova_quantita = serializers.IntegerField(min_value=0)


class RettificaSilosSerializer(serializers.Serializer):
    """Per impostare la quantità assoluta di litri in un silos con logging."""
    tipologia_vino_id = serializers.IntegerField()
    nuova_quantita_litri = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)


# ─── Clienti / Agenti ─────────────────────────────────────────────────────

class ClienteSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()

    def get_label(self, obj):
        return str(obj)

    class Meta:
        model = Cliente
        fields = '__all__'


class AgenteSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()
    nominativo = serializers.SerializerMethodField()

    def get_label(self, obj):
        return str(obj)

    def get_nominativo(self, obj):
        return f"{obj.cognome} {obj.nome}"

    class Meta:
        model = Agente
        fields = '__all__'


# ─── Ordini ───────────────────────────────────────────────────────────────

class RigaOrdineBottigliaSerializer(serializers.ModelSerializer):
    tipologia_vino_nome = serializers.SerializerMethodField()
    famiglia_nome = serializers.CharField(source='tipologia_vino.famiglia.nome', read_only=True)
    subtotale = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    def get_tipologia_vino_nome(self, obj):
        return str(obj.tipologia_vino) if obj.tipologia_vino else None

    class Meta:
        model = RigaOrdineBottiglia
        fields = [
            'id', 'tipologia_vino', 'tipologia_vino_nome', 'famiglia_nome',
            'ha_etichetta', 'ha_capsula', 'quantita', 'prezzo_unitario', 'subtotale',
        ]


class RigaOrdineGadgetSerializer(serializers.ModelSerializer):
    tipo_gadget_nome = serializers.CharField(source='tipo_gadget.nome', read_only=True)

    class Meta:
        model = RigaOrdineGadget
        fields = ['id', 'tipo_gadget', 'tipo_gadget_nome', 'quantita']


class OrdineSerializer(serializers.ModelSerializer):
    """Serializer per la lista degli ordini (lightweight) e per la lettura completa."""
    righe_bottiglie = RigaOrdineBottigliaSerializer(many=True, read_only=True)
    righe_gadget = RigaOrdineGadgetSerializer(many=True, read_only=True)

    cliente_label = serializers.SerializerMethodField()
    cliente_dati = serializers.SerializerMethodField()
    agente_label = serializers.SerializerMethodField()
    agente_dati = serializers.SerializerMethodField()

    stato_display = serializers.CharField(source='get_stato_display', read_only=True)

    imponibile_lordo = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    importo_sconto = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    imponibile_netto = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    importo_iva = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    totale = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    def get_cliente_label(self, obj):
        return str(obj.cliente) if obj.cliente else None

    def get_cliente_dati(self, obj):
        if not obj.cliente:
            return None
        c = obj.cliente
        return {
            'id': c.id, 'nome': c.nome, 'azienda': c.azienda,
            'via': c.via, 'partita_iva': c.partita_iva,
            'telefono': c.telefono, 'email': c.email,
        }

    def get_agente_label(self, obj):
        return str(obj.agente) if obj.agente else None

    def get_agente_dati(self, obj):
        if not obj.agente:
            return None
        a = obj.agente
        return {
            'id': a.id, 'nome': a.nome, 'cognome': a.cognome,
            'telefono': a.telefono, 'email': a.email,
        }

    class Meta:
        model = Ordine
        fields = [
            'id', 'numero', 'data', 'data_aggiornamento',
            'cliente', 'cliente_label', 'cliente_dati',
            'agente', 'agente_label', 'agente_dati',
            'sconto_percentuale', 'aliquota_iva',
            'tracking_number', 'pacco_arrivato', 'fattura_pagata',
            'stato', 'stato_display', 'data_annullamento', 'note',
            'righe_bottiglie', 'righe_gadget',
            'imponibile_lordo', 'importo_sconto', 'imponibile_netto',
            'importo_iva', 'totale',
        ]
        read_only_fields = ['numero', 'data', 'data_aggiornamento', 'data_annullamento', 'stato']


# ── Serializer dedicato per CREARE un ordine (con righe inline) ───────────

class RigaOrdineBottigliaInputSerializer(serializers.Serializer):
    tipologia_vino_id = serializers.IntegerField()
    ha_etichetta = serializers.BooleanField(default=True)
    ha_capsula = serializers.BooleanField(default=True)
    quantita = serializers.IntegerField(min_value=1)
    prezzo_unitario = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0'))


class RigaOrdineGadgetInputSerializer(serializers.Serializer):
    tipo_gadget_id = serializers.IntegerField()
    quantita = serializers.IntegerField(min_value=1)


class OrdineCreateSerializer(serializers.Serializer):
    cliente_id = serializers.IntegerField()
    agente_id = serializers.IntegerField(required=False, allow_null=True)
    sconto_percentuale = serializers.DecimalField(
        max_digits=5, decimal_places=2,
        min_value=Decimal('0'), max_value=Decimal('100'),
        default=Decimal('0'),
    )
    aliquota_iva = serializers.DecimalField(
        max_digits=5, decimal_places=2,
        min_value=Decimal('0'), default=Decimal('22'),
    )
    tracking_number = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')
    pacco_arrivato = serializers.BooleanField(default=False)
    fattura_pagata = serializers.BooleanField(default=False)
    note = serializers.CharField(required=False, allow_blank=True, default='')

    righe_bottiglie = RigaOrdineBottigliaInputSerializer(many=True)
    righe_gadget = RigaOrdineGadgetInputSerializer(many=True, required=False, default=list)

    def validate_righe_bottiglie(self, value):
        if not value:
            raise serializers.ValidationError("L'ordine deve contenere almeno una bottiglia.")
        return value


# ── Endpoint helper: bottiglie disponibili in magazzino ───────────────────

class BottiglieDisponibiliSerializer(serializers.Serializer):
    """Output dell'endpoint che lista le bottiglie disponibili per la creazione ordine."""
    tipologia_vino_id = serializers.IntegerField()
    tipologia_vino_nome = serializers.CharField()
    famiglia_nome = serializers.CharField()
    ha_etichetta = serializers.BooleanField()
    ha_capsula = serializers.BooleanField()
    quantita_totale = serializers.IntegerField()

