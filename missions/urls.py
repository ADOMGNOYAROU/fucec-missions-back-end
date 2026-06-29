from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views_vehicules import VehiculeViewSet, ChauffeurViewSet

app_name = 'missions'

# Création d'un routeur DRF
router = DefaultRouter()
router.register(r'missions', views.MissionViewSet, basename='mission')
router.register(r'vehicules', VehiculeViewSet, basename='vehicule')
router.register(r'chauffeurs', ChauffeurViewSet, basename='chauffeur')
router.register(r'validations', views.ValidationViewSet, basename='validation')
router.register(r'justificatifs', views.JustificatifViewSet, basename='justificatif')

urlpatterns = [
    # Inclure les vues du routeur
    path('', include(router.urls)),
    
    # Autres vues personnalisées
    path('missions/<int:pk>/submit/', views.MissionSubmitView.as_view(), name='mission-submit'),
    path('missions/<int:pk>/validate/<str:decision>/', views.ValidateMissionView.as_view(), 
         name='validate-mission'),
    path('missions/<int:pk>/declare-return/', views.MissionDeclareReturnView.as_view(), 
         name='mission-declare-return'),
    path('missions/<int:pk>/submit-justificatifs/', 
         views.MissionSubmitJustificatifsView.as_view(), 
         name='mission-submit-justificatifs'),
    path('missions/<int:pk>/verify-justificatifs/',
         views.JustificatifVerifyView.as_view(),
         name='verify-justificatifs'),
    path('justificatifs/<int:justificatif_id>/validate/<str:decision>/',
         views.ValidateJustificatifView.as_view(),
         name='validate-justificatif'),

    # Validations
    path('validations/<int:pk>/decide/', views.ValidationDecideView.as_view(), name='validation-decide'),
    
    # Signatures financières
    path('signatures/', views.SignatureListView.as_view(), name='signature-list'),
    path('signatures/<int:pk>/sign/', views.SignatureFinanciereView.as_view(), name='signature-sign'),
    
    # Avances
    path('avances/', views.AvanceListCreateView.as_view(), name='avance-list'),
    path('avances/<int:pk>/', views.AvanceDetailView.as_view(), name='avance-detail'),
    
    # Notifications
    path('notifications/', views.NotificationListView.as_view(), name='notification-list'),
    
    # Statistiques
    path('stats/', views.mission_stats, name='mission-stats'),
    path('delegations/<int:pk>/', views.DelegationDetailView.as_view(), name='delegation-detail'),
    
    # Rapports finaux
    path('rapports-finaux/', views.RapportFinalListCreateView.as_view(), name='rapport-final-list'),
    path('rapports-finaux/<int:pk>/', views.RapportFinalDetailView.as_view(), name='rapport-final-detail'),
    path('rapports-finaux/<int:pk>/validate/', views.RapportFinalValidateView.as_view(), name='rapport-final-validate'),
    
    # Historique
    path('historique/', views.HistoriqueMissionListView.as_view(), name='historique-list'),
    
    # Workflow validation config
    path('workflow-validation/', views.WorkflowValidationListCreateView.as_view(), name='workflow-validation-list'),
    path('workflow-validation/<int:pk>/', views.WorkflowValidationDetailView.as_view(), name='workflow-validation-detail'),
    
    # Types de mission
    path('types-mission/', views.TypeMissionListCreateView.as_view(), name='type-mission-list'),
    path('types-mission/<int:pk>/', views.TypeMissionDetailView.as_view(), name='type-mission-detail'),
    
    # Types de frais
    path('types-frais/', views.TypeFraisListCreateView.as_view(), name='type-frais-list'),
    path('types-frais/<int:pk>/', views.TypeFraisDetailView.as_view(), name='type-frais-detail'),
    
    # Véhicules
    path('vehicules/', views.VehiculeListCreateView.as_view(), name='vehicule-list'),
    path('vehicules/<int:pk>/', views.VehiculeDetailView.as_view(), name='vehicule-detail'),
    
    # Barèmes kilométriques
    path('baremes/', views.BaremeListCreateView.as_view(), name='bareme-list'),
    path('baremes/<int:pk>/', views.BaremeDetailView.as_view(), name='bareme-detail'),
]
