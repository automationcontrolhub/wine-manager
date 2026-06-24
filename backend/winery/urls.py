from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import dashboard_ordini as dord

router = DefaultRouter()
router.register(r'tipo-cartone', views.TipoCartoneViewSet)
router.register(r'tipo-tappo', views.TipoTappoViewSet)
router.register(r'tipo-bottiglia', views.TipoBottigliaViewSet)
router.register(r'tipo-etichetta', views.TipoEtichettaViewSet)
router.register(r'tipo-capsula', views.TipoCapsulaViewSet)
router.register(r'tipo-cestello', views.TipoCestelloViewSet)
router.register(r'tipo-gadget', views.TipoGadgetViewSet)
router.register(r'famiglie', views.FamigliaVinoViewSet)
router.register(r'tipologie-vino', views.TipologiaVinoViewSet)
router.register(r'lotti', views.LottoBottiglieViewSet)
router.register(r'movimenti', views.MovimentoMagazzinoViewSet)
router.register(r'operazioni', views.OperazioneImbottigliamentoViewSet)
router.register(r'clienti', views.ClienteViewSet)
router.register(r'agenti', views.AgenteViewSet)
router.register(r'ordini', views.OrdineViewSet)
router.register(r'paesi', views.PaeseViewSet, basename='paese')
router.register(r'regioni', views.RegioneViewSet, basename='regione')
router.register(r'province', views.ProvinciaViewSet, basename='provincia')
router.register(r'citta', views.CittaViewSet, basename='citta')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', views.dashboard),
    path('aggiunta-vino/', views.aggiunta_vino),
    path('carico-magazzino/', views.carico_magazzino),
    path('rettifica-magazzino/', views.rettifica_magazzino),
    path('rettifica-silos/', views.rettifica_silos),
    path('crea-senza-etichetta/', views.crea_bottiglie_senza_etichetta),
    path('crea-con-etichetta/', views.crea_bottiglie_con_etichetta),
    path('associa-etichetta/', views.associa_etichetta),
    path('bottiglie-senza-etichetta/', views.bottiglie_senza_etichetta),
    path('bottiglie-disponibili/', views.bottiglie_disponibili),
    path('operazioni/<int:pk>/annulla/', views.annulla_operazione),

    # ─── Dashboard Ordini ─────────────────────────────────────────────
    path('dashboard-ordini/filtri/', dord.dashboard_ordini_filtri),
    path('dashboard-ordini/commerciale/', dord.dashboard_ordini_commerciale),
    path('dashboard-ordini/clienti/', dord.dashboard_ordini_clienti),
    path('dashboard-ordini/agenti/', dord.dashboard_ordini_agenti),
    path('dashboard-ordini/prodotti/', dord.dashboard_ordini_prodotti),
    path('dashboard-ordini/pagamenti/', dord.dashboard_ordini_pagamenti),
]

