from django.contrib import admin
from .models import (
    TipoCartone, TipoTappo, TipoBottiglia, TipoEtichetta,
    TipoCapsula, TipoCestello, FamigliaVino, TipologiaVino,
    LottoBottiglie, MovimentoMagazzino,
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
