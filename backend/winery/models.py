from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator


# ─── MATERIALI (tipologie gestite dall'utente) ─────────────────────────────

class TipoCartone(models.Model):
    """Tipologia di cartone — es: Normale 6 bott. 0.75, Spumante, ecc."""
    nome = models.CharField(max_length=120, unique=True)
    capacita_bottiglie = models.PositiveIntegerField(
        help_text="Quante bottiglie contiene (es: 6 per vino, 1 per spumante)"
    )
    quantita = models.PositiveIntegerField(default=0, help_text="Scorta in magazzino")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Tipi cartone"
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.capacita_bottiglie} bott.)"


class TipoTappo(models.Model):
    """Tipologia di tappo — es: Diam5, Diam10, Spumante, ecc."""
    nome = models.CharField(max_length=120, unique=True)
    quantita = models.PositiveIntegerField(default=0, help_text="Scorta in magazzino")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Tipi tappo"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class TipoBottiglia(models.Model):
    """Tipologia di bottiglia — es: Tipo 1 0.75L, Spumante, ecc."""
    nome = models.CharField(max_length=120, unique=True)
    capacita_litri = models.DecimalField(max_digits=5, decimal_places=2, help_text="Capacità in litri")
    quantita = models.PositiveIntegerField(default=0, help_text="Scorta in magazzino")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Tipi bottiglia"
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.capacita_litri}L)"


class TipoEtichetta(models.Model):
    """Tipologia di etichetta — es: Tipo 1 0.75L, Tipo spumante, ecc."""
    nome = models.CharField(max_length=120, unique=True)
    quantita = models.PositiveIntegerField(default=0, help_text="Scorta in magazzino")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Tipi etichetta"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class TipoCapsula(models.Model):
    """Tipologia di capsula — es: Tipo 1, Spumante, ecc."""
    nome = models.CharField(max_length=120, unique=True)
    quantita = models.PositiveIntegerField(default=0, help_text="Scorta in magazzino")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Tipi capsula"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class TipoCestello(models.Model):
    """Tipologia di cestello (solo spumante)."""
    nome = models.CharField(max_length=120, unique=True)
    quantita = models.PositiveIntegerField(default=0, help_text="Scorta in magazzino")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Tipi cestello"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class TipoGadget(models.Model):
    """Tipologia di gadget — es: Apribottiglie, Sacchetto regalo, ecc."""
    nome = models.CharField(max_length=120, unique=True)
    quantita = models.PositiveIntegerField(default=0, help_text="Scorta in magazzino")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Tipi gadget"
        ordering = ['nome']

    def __str__(self):
        return self.nome


# ─── FAMIGLIA e TIPOLOGIA VINO ────────────────────────────────────────────

class FamigliaVino(models.Model):
    """
    Famiglia/categoria — es: Spumante, Etna DOC, Contrade, Cru.
    """
    nome = models.CharField(max_length=120, unique=True)
    is_spumante = models.BooleanField(default=False, help_text="Se True, richiede cestello")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Famiglie vino"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class TipologiaVino(models.Model):
    """
    Una specifica tipologia di vino — es: Etna DOC Rosso, SN35 Brut Nature.
    Ogni tipologia ha associati i materiali specifici da usare per l'imbottigliamento.
    Il vino si trova in un silos con una quantità in litri.
    """
    nome = models.CharField(max_length=200)
    famiglia = models.ForeignKey(FamigliaVino, on_delete=models.CASCADE, related_name='tipologie')
    quantita_litri = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        help_text="Litri disponibili nel silos"
    )

    # Materiali associati
    tipo_cartone = models.ForeignKey(TipoCartone, on_delete=models.PROTECT, related_name='+')
    tipo_tappo = models.ForeignKey(TipoTappo, on_delete=models.PROTECT, related_name='+')
    tipo_bottiglia = models.ForeignKey(TipoBottiglia, on_delete=models.PROTECT, related_name='+')
    tipo_etichetta = models.ForeignKey(TipoEtichetta, on_delete=models.PROTECT, related_name='+')
    tipo_capsula = models.ForeignKey(TipoCapsula, on_delete=models.PROTECT, related_name='+')
    tipo_cestello = models.ForeignKey(
        TipoCestello, on_delete=models.PROTECT, related_name='+',
        null=True, blank=True,
        help_text="Solo per spumante"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Tipologie vino"
        ordering = ['famiglia__nome', 'nome']
        unique_together = ['nome', 'famiglia']

    def __str__(self):
        return f"{self.famiglia.nome} — {self.nome}"


# ─── LOTTI BOTTIGLIE ──────────────────────────────────────────────────────

class LottoBottiglie(models.Model):
    """
    Ogni riga rappresenta un lotto di N bottiglie con le stesse caratteristiche.
    
    Flusso:
    1. Creazione SENZA etichetta → ha_etichetta=False, quantita=N
    2. Associazione etichetta → scala da lotto senza etichetta, crea/incrementa lotto con etichetta
    3. Creazione CON etichetta → ha_etichetta=True direttamente
    
    La capsula può essere applicata in step 1 o in step 2 (flag).
    """

    class Stato(models.TextChoices):
        SENZA_ETICHETTA = 'SENZA_ETICHETTA', 'Senza etichetta'
        COMPLETA = 'COMPLETA', 'Completa'

    tipologia_vino = models.ForeignKey(TipologiaVino, on_delete=models.PROTECT, related_name='lotti')
    quantita = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    stato = models.CharField(max_length=20, choices=Stato.choices, default=Stato.SENZA_ETICHETTA)
    ha_etichetta = models.BooleanField(default=False)
    ha_capsula = models.BooleanField(default=False)
    data_creazione = models.DateTimeField(auto_now_add=True)
    data_aggiornamento = models.DateTimeField(auto_now=True)
    note = models.TextField(blank=True, default='')

    class Meta:
        verbose_name_plural = "Lotti bottiglie"
        ordering = ['-data_creazione']

    def __str__(self):
        label = self.tipologia_vino
        stato = "✓" if self.ha_etichetta else "◯"
        return f"{label} × {self.quantita} [{stato}]"


# ─── MOVIMENTI MAGAZZINO ──────────────────────────────────────────────────

class MovimentoMagazzino(models.Model):
    """
    Log di ogni movimento di magazzino per tracciabilità.
    """

    class TipoMovimento(models.TextChoices):
        CARICO = 'CARICO', 'Carico'
        SCARICO = 'SCARICO', 'Scarico (imbottigliamento)'
        AGGIUNTA_VINO = 'AGGIUNTA_VINO', 'Aggiunta vino al silos'
        ANNULLAMENTO = 'ANNULLAMENTO', 'Annullamento operazione'
        ORDINE_SCARICO = 'ORDINE_SCARICO', 'Scarico per ordine'
        ORDINE_RIPRISTINO = 'ORDINE_RIPRISTINO', 'Ripristino per annullamento ordine'

    class Categoria(models.TextChoices):
        TAPPO = 'TAPPO', 'Tappo'
        CARTONE = 'CARTONE', 'Cartone'
        BOTTIGLIA = 'BOTTIGLIA', 'Bottiglia'
        ETICHETTA = 'ETICHETTA', 'Etichetta'
        CAPSULA = 'CAPSULA', 'Capsula'
        CESTELLO = 'CESTELLO', 'Cestello'
        GADGET = 'GADGET', 'Gadget'
        VINO = 'VINO', 'Vino (litri)'

    tipo = models.CharField(max_length=20, choices=TipoMovimento.choices)
    categoria = models.CharField(max_length=20, choices=Categoria.choices)
    quantita = models.DecimalField(max_digits=12, decimal_places=2)
    descrizione = models.TextField(blank=True)
    data = models.DateTimeField(auto_now_add=True)

    # Riferimenti generici (opzionali)
    riferimento_id = models.PositiveIntegerField(null=True, blank=True)
    riferimento_tipo = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name_plural = "Movimenti magazzino"
        ordering = ['-data']

    def __str__(self):
        return f"{self.tipo} {self.categoria} × {self.quantita} — {self.data:%d/%m/%Y}"


# ─── OPERAZIONI IMBOTTIGLIAMENTO (per annullamento) ───────────────────────

class OperazioneImbottigliamento(models.Model):
    """
    Snapshot di ogni operazione di imbottigliamento, per permettere l'annullamento.
    Memorizza tutto ciò che è stato consumato/prodotto, in modo da poterlo invertire.
    """

    class TipoOperazione(models.TextChoices):
        CREA_SENZA_ETICHETTA = 'CREA_SENZA_ETICHETTA', 'Crea senza etichetta'
        CREA_CON_ETICHETTA = 'CREA_CON_ETICHETTA', 'Crea con etichetta'
        ASSOCIA_ETICHETTA = 'ASSOCIA_ETICHETTA', 'Associa etichetta'

    class Stato(models.TextChoices):
        ATTIVA = 'ATTIVA', 'Attiva'
        ANNULLATA = 'ANNULLATA', 'Annullata'

    tipo = models.CharField(max_length=30, choices=TipoOperazione.choices)
    stato = models.CharField(max_length=20, choices=Stato.choices, default=Stato.ATTIVA)
    data = models.DateTimeField(auto_now_add=True)
    data_annullamento = models.DateTimeField(null=True, blank=True)

    # Tipologie coinvolte (origine = sempre, destinazione solo per associa etichetta)
    tipologia_vino = models.ForeignKey(
        TipologiaVino, on_delete=models.PROTECT, related_name='operazioni'
    )
    tipologia_vino_destinazione = models.ForeignKey(
        TipologiaVino, on_delete=models.PROTECT, related_name='operazioni_dest',
        null=True, blank=True
    )

    quantita = models.PositiveIntegerField()
    con_etichetta = models.BooleanField(default=False)
    con_capsula = models.BooleanField(default=False)

    # Snapshot completo dei consumi (per l'annullamento)
    # JSON con: vino_litri, bottiglie, tappi, etichette, capsule, cartoni, cestelli
    # e i dettagli per tipo (es: capsule_da_aggiungere per associa etichetta)
    dettagli = models.JSONField(default=dict)

    note = models.TextField(blank=True, default='')

    class Meta:
        verbose_name_plural = "Operazioni imbottigliamento"
        ordering = ['-data']

    def __str__(self):
        return f"{self.get_tipo_display()} × {self.quantita} — {self.tipologia_vino} ({self.get_stato_display()})"


# ─── GEOGRAFIA ────────────────────────────────────────────────────────────

class Paese(models.Model):
    nome = models.CharField(max_length=120, unique=True)
    codice_iso = models.CharField(max_length=3, blank=True, default='',
                                  help_text="Codice ISO 3166-1 alpha-2 o alpha-3")

    class Meta:
        verbose_name_plural = "Paesi"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Regione(models.Model):
    paese = models.ForeignKey(Paese, on_delete=models.CASCADE, related_name='regioni')
    nome = models.CharField(max_length=120)
    codice_istat = models.CharField(max_length=10, blank=True, default='')

    class Meta:
        verbose_name_plural = "Regioni"
        ordering = ['nome']
        unique_together = ['paese', 'nome']

    def __str__(self):
        return self.nome


class Provincia(models.Model):
    regione = models.ForeignKey(Regione, on_delete=models.CASCADE, related_name='province')
    nome = models.CharField(max_length=120)
    sigla = models.CharField(max_length=5, blank=True, default='')
    codice_istat = models.CharField(max_length=10, blank=True, default='')

    class Meta:
        verbose_name_plural = "Province"
        ordering = ['nome']
        unique_together = ['regione', 'nome']

    def __str__(self):
        if self.sigla:
            return f"{self.nome} ({self.sigla})"
        return self.nome


class Citta(models.Model):
    provincia = models.ForeignKey(Provincia, on_delete=models.CASCADE, related_name='citta')
    nome = models.CharField(max_length=200)
    codice_istat = models.CharField(max_length=10, blank=True, default='')
    codice_catastale = models.CharField(max_length=10, blank=True, default='')
    cap_list = models.JSONField(default=list, help_text="Lista CAP disponibili per la città")

    class Meta:
        verbose_name_plural = "Città"
        ordering = ['nome']
        unique_together = ['provincia', 'nome']

    def __str__(self):
        return self.nome


# ─── ANAGRAFICHE: Clienti e Agenti ────────────────────────────────────────

class Cliente(models.Model):
    """Anagrafica cliente (azienda o privato)."""
    nome = models.CharField(max_length=200, help_text="Nome referente / privato")
    azienda = models.CharField(max_length=200, blank=True, default='')

    # Indirizzo strutturato
    paese = models.ForeignKey(Paese, on_delete=models.PROTECT,
                              related_name='clienti', null=True, blank=True)
    regione = models.ForeignKey(Regione, on_delete=models.PROTECT,
                                related_name='clienti', null=True, blank=True)
    provincia = models.ForeignKey(Provincia, on_delete=models.PROTECT,
                                  related_name='clienti', null=True, blank=True)
    citta = models.ForeignKey(Citta, on_delete=models.PROTECT,
                              related_name='clienti', null=True, blank=True)
    cap = models.CharField(max_length=10, blank=True, default='')
    via = models.CharField(max_length=300, blank=True, default='',
                           help_text="Via, numero civico")

    # Campo legacy per dati pre-migrazione
    legacy_indirizzo = models.CharField(max_length=300, blank=True, default='',
                                        help_text="Indirizzo legacy (per dati pre-migrazione geografica)")

    partita_iva = models.CharField(max_length=30, blank=True, default='')
    telefono = models.CharField(max_length=30, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    note = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Clienti"
        ordering = ['azienda', 'nome']

    def __str__(self):
        if self.azienda:
            return f"{self.azienda} — {self.nome}"
        return self.nome


class Agente(models.Model):
    """Anagrafica agente/rappresentante associabile a un ordine."""
    nome = models.CharField(max_length=120)
    cognome = models.CharField(max_length=120)
    telefono = models.CharField(max_length=30, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    note = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Agenti"
        ordering = ['cognome', 'nome']

    def __str__(self):
        return f"{self.cognome} {self.nome}"


# ─── ORDINI ───────────────────────────────────────────────────────────────

class Ordine(models.Model):
    """
    Ordine cliente. Quando in stato CONFERMATO scarica dal magazzino bottiglie
    e gadget. Se ANNULLATO ripristina le quantità.
    """

    class Stato(models.TextChoices):
        CONFERMATO = 'CONFERMATO', 'Confermato'
        ANNULLATO = 'ANNULLATO', 'Annullato'

    numero = models.PositiveIntegerField(unique=True, editable=False)
    data = models.DateTimeField(auto_now_add=True)
    data_aggiornamento = models.DateTimeField(auto_now=True)

    cliente = models.ForeignKey(
        Cliente, on_delete=models.PROTECT, related_name='ordini'
    )
    agente = models.ForeignKey(
        Agente, on_delete=models.SET_NULL, null=True, blank=True, related_name='ordini'
    )

    sconto_percentuale = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0'),
        validators=[MinValueValidator(0)],
        help_text="Sconto applicato sul totale (es: 10 = 10%)"
    )
    aliquota_iva = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('22'),
        validators=[MinValueValidator(0)],
        help_text="Aliquota IVA in percentuale (es: 22 = 22%)"
    )

    tracking_number = models.CharField(max_length=100, blank=True, default='')
    pacco_arrivato = models.BooleanField(default=False)
    fattura_pagata = models.BooleanField(default=False)

    stato = models.CharField(max_length=20, choices=Stato.choices, default=Stato.CONFERMATO)
    data_annullamento = models.DateTimeField(null=True, blank=True)

    note = models.TextField(blank=True, default='')

    class Meta:
        verbose_name_plural = "Ordini"
        ordering = ['-data']

    def __str__(self):
        return f"Ordine #{self.numero} — {self.cliente}"

    def save(self, *args, **kwargs):
        if not self.pk and not self.numero:
            last = Ordine.objects.order_by('-numero').first()
            self.numero = (last.numero + 1) if last else 1
        super().save(*args, **kwargs)

    # --- Calcoli totali (proprietà a runtime) -----------------------------

    @property
    def imponibile_lordo(self):
        """Somma dei subtotali delle righe bottiglie (prezzo × quantità), senza sconto e senza IVA."""
        totale = Decimal('0')
        for riga in self.righe_bottiglie.all():
            totale += riga.subtotale
        return totale

    @property
    def importo_sconto(self):
        return (self.imponibile_lordo * self.sconto_percentuale / Decimal('100')).quantize(Decimal('0.01'))

    @property
    def imponibile_netto(self):
        """Imponibile dopo lo sconto, senza IVA."""
        return (self.imponibile_lordo - self.importo_sconto).quantize(Decimal('0.01'))

    @property
    def importo_iva(self):
        return (self.imponibile_netto * self.aliquota_iva / Decimal('100')).quantize(Decimal('0.01'))

    @property
    def totale(self):
        """Totale finale IVA inclusa."""
        return (self.imponibile_netto + self.importo_iva).quantize(Decimal('0.01'))


class RigaOrdineBottiglia(models.Model):
    """Riga di un ordine relativa a un tipo di bottiglia (vino completo)."""
    ordine = models.ForeignKey(
        Ordine, on_delete=models.CASCADE, related_name='righe_bottiglie'
    )
    tipologia_vino = models.ForeignKey(
        TipologiaVino, on_delete=models.PROTECT, related_name='+'
    )
    ha_etichetta = models.BooleanField(default=True)
    ha_capsula = models.BooleanField(default=True)
    quantita = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    prezzo_unitario = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))]
    )

    class Meta:
        verbose_name_plural = "Righe ordine bottiglie"

    def __str__(self):
        eti = "etichettata" if self.ha_etichetta else "non etichettata"
        return f"{self.tipologia_vino} ({eti}) × {self.quantita}"

    @property
    def subtotale(self):
        return (Decimal(self.quantita) * self.prezzo_unitario).quantize(Decimal('0.01'))


class RigaOrdineGadget(models.Model):
    """Riga di un ordine relativa a un gadget omaggio (no prezzo)."""
    ordine = models.ForeignKey(
        Ordine, on_delete=models.CASCADE, related_name='righe_gadget'
    )
    tipo_gadget = models.ForeignKey(
        TipoGadget, on_delete=models.PROTECT, related_name='+'
    )
    quantita = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        verbose_name_plural = "Righe ordine gadget"

    def __str__(self):
        return f"{self.tipo_gadget} × {self.quantita}"
