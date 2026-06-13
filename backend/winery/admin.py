from django.contrib import admin
from .models import (
    TipoCartone, TipoTappo, TipoBottiglia, TipoEtichetta,
    TipoCapsula, TipoCestello, TipoGadget, FamigliaVino, TipologiaVino,
    LottoBottiglie, MovimentoMagazzino, OperazioneImbottigliamento,
    Cliente, Agente, Ordine, RigaOrdineBottiglia, RigaOrdineGadget,
)

@admin.register(TipoCartone)
class TipoCartoneAdmin(admin.ModelAdmin):
    list_display = ['nome', 'capacita_bottiglie', 'quantita']

@admin.register(TipoTappo)
class TipoTappoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'quantita']

@admin.register(TipoBottiglia)
class TipoBottigliaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'capacita_litri', 'quantita']

@admin.register(TipoEtichetta)
class TipoEtichettaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'quantita']

@admin.register(TipoCapsula)
class TipoCapsulaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'quantita']

@admin.register(TipoCestello)
class TipoCestelloAdmin(admin.ModelAdmin):
    list_display = ['nome', 'quantita']

@admin.register(TipoGadget)
class TipoGadgetAdmin(admin.ModelAdmin):
    list_display = ['nome', 'quantita']

@admin.register(FamigliaVino)
class FamigliaVinoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'is_spumante']

@admin.register(TipologiaVino)
class TipologiaVinoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'famiglia', 'quantita_litri']
    list_filter = ['famiglia']

@admin.register(LottoBottiglie)
class LottoBottiglieAdmin(admin.ModelAdmin):
    list_display = ['tipologia_vino', 'quantita', 'stato', 'ha_etichetta', 'ha_capsula', 'data_creazione']
    list_filter = ['stato', 'ha_etichetta']

@admin.register(MovimentoMagazzino)
class MovimentoMagazzinoAdmin(admin.ModelAdmin):
    list_display = ['tipo', 'categoria', 'quantita', 'data', 'descrizione']
    list_filter = ['tipo', 'categoria']

@admin.register(OperazioneImbottigliamento)
class OperazioneImbottigliamentoAdmin(admin.ModelAdmin):
    list_display = ['tipo', 'tipologia_vino', 'quantita', 'stato', 'data']
    list_filter = ['tipo', 'stato']


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['azienda', 'nome', 'partita_iva', 'telefono']
    search_fields = ['azienda', 'nome', 'partita_iva']


@admin.register(Agente)
class AgenteAdmin(admin.ModelAdmin):
    list_display = ['cognome', 'nome', 'telefono']
    search_fields = ['cognome', 'nome']


class RigaOrdineBottigliaInline(admin.TabularInline):
    model = RigaOrdineBottiglia
    extra = 0


class RigaOrdineGadgetInline(admin.TabularInline):
    model = RigaOrdineGadget
    extra = 0


@admin.register(Ordine)
class OrdineAdmin(admin.ModelAdmin):
    list_display = ['numero', 'data', 'cliente', 'agente', 'stato',
                    'pacco_arrivato', 'fattura_pagata']
    list_filter = ['stato', 'pacco_arrivato', 'fattura_pagata']
    search_fields = ['numero', 'cliente__nome', 'cliente__azienda', 'tracking_number']
    inlines = [RigaOrdineBottigliaInline, RigaOrdineGadgetInline]
    readonly_fields = ['numero', 'data', 'data_aggiornamento', 'data_annullamento']