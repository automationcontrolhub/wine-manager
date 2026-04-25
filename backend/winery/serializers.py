from rest_framework import serializers
from .models import (
    TipoCartone, TipoTappo, TipoBottiglia, TipoEtichetta,
    TipoCapsula, TipoCestello, FamigliaVino, TipologiaVino,
    LottoBottiglie, MovimentoMagazzino,
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


# ─── Vino ─────────────────────────────────────────────────────────────────

class FamigliaVinoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamigliaVino
        fields = '__all__'


class TipologiaVinoSerializer(serializers.ModelSerializer):
    famiglia_nome = serializers.CharField(source='famiglia.nome', read_only=True)
    famiglia_is_spumante = serializers.BooleanField(source='famiglia.is_spumante', read_only=True)
    tipo_cartone_nome = serializers.CharField(source='tipo_cartone.nome', read_only=True)
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
    litri = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0.01)


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
        'cartone', 'tappo', 'bottiglia', 'etichetta', 'capsula', 'cestello'
    ])
    tipo_id = serializers.IntegerField()
    quantita = serializers.IntegerField(min_value=1)
