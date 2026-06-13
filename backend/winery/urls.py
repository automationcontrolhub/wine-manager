from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

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
]

