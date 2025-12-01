"""
URL configuration for fucec_missions project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Redirige la racine vers l'admin
    path('', RedirectView.as_view(url='/admin/', permanent=True)),
    
    # URLs de l'admin
    path('admin/', admin.site.urls),
    
    # API URLs
    path('api/', include([
        # Users app
        path('users/', include('users.urls')),
        
        # Missions app
        path('missions/', include('missions.urls')),
        
        # Add other API endpoints here
    ])),
    
    # API Auth
    path('api/auth/', include('rest_framework.urls', namespace='rest_framework')),
]

# Ajout des URLs pour les fichiers statiques et médias en mode DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
