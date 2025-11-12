from django.urls import path
from . import views

app_name = 'missions'

urlpatterns = [
    # Missions
    path('', views.MissionListView.as_view(), name='mission-list'),
    path('<int:pk>/', views.MissionDetailView.as_view(), name='mission-detail'),
    path('<int:pk>/submit/', views.MissionSubmitView.as_view(), name='mission-submit'),
    path('<int:pk>/declare-return/', views.MissionDeclareReturnView.as_view(), name='mission-declare-return'),
    path('<int:pk>/submit-justificatifs/', views.MissionSubmitJustificatifsView.as_view(), name='mission-submit-justificatifs'),
    path('<int:pk>/verify-justificatifs/', views.JustificatifVerifyView.as_view(), name='verify-justificatifs'),

    # Validations
    path('<int:mission_id>/validate/<str:decision>/', views.ValidateMissionView.as_view(), name='validate-mission'),
    path('validations/', views.ValidationListView.as_view(), name='validation-list'),
    path('validations/<int:pk>/decide/', views.ValidationDecideView.as_view(), name='validation-decide'),

    # Signatures financières
    path('signatures/', views.SignatureListView.as_view(), name='signature-list'),
    path('signatures/<int:pk>/sign/', views.SignatureFinanciereView.as_view(), name='signature-sign'),

    # Avances
    path('avances/', views.AvanceListCreateView.as_view(), name='avance-list'),
    path('avances/<int:pk>/', views.AvanceDetailView.as_view(), name='avance-detail'),

    # Notifications
    path('notifications/', views.NotificationListView.as_view(), name='notification-list'),

    # Justificatifs
    path('justificatifs/', views.JustificatifListView.as_view(), name='justificatif-list'),
    path('justificatifs/<int:pk>/', views.JustificatifDetailView.as_view(), name='justificatif-detail'),
    path('justificatifs/<int:justificatif_id>/validate/<str:decision>/', views.ValidateJustificatifView.as_view(), name='validate-justificatif'),

    # Statistiques
    path('stats/', views.mission_stats, name='mission-stats'),
]
