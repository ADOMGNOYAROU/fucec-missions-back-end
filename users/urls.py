from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter

from . import views
from .views import LoginView, AgentViewSet, ChefAgenceViewSet, ResponsableCopecViewSet, DGViewSet, RHViewSet, ComptableViewSet, DirecteurFinancesViewSet, ChauffeurViewSet, AdminViewSet

app_name = 'users'

router = DefaultRouter()
router.register(r'agents', AgentViewSet, basename='agents')
router.register(r'chefs-agence', ChefAgenceViewSet, basename='chefs-agence')
router.register(r'responsables-copec', ResponsableCopecViewSet, basename='responsables-copec')
router.register(r'dg', DGViewSet, basename='dg')
router.register(r'rh', RHViewSet, basename='rh')
router.register(r'comptables', ComptableViewSet, basename='comptables')
router.register(r'directeurs-finances', DirecteurFinancesViewSet, basename='directeurs-finances')
router.register(r'chauffeurs', ChauffeurViewSet, basename='chauffeurs')
router.register(r'admins', AdminViewSet, basename='admins')

urlpatterns = [
    # Authentification
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='token_obtain_pair'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Profil utilisateur
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/change-password/', views.ChangePasswordView.as_view(), name='change-password'),

    # Gestion des utilisateurs
    path('users/', views.UserListView.as_view(), name='user-list'),
    path('users/subordinates/', views.SubordinatesView.as_view(), name='subordinates'),

    path('', include(router.urls)),
]
