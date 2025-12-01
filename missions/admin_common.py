from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models_vehicules import Vehicule, Bareme
from .models_documents import EtatDepenses, Notification, AuditLog

@admin.register(Vehicule)
class VehiculeAdmin(admin.ModelAdmin):
    list_display = ('immatriculation', 'marque', 'modele', 'type', 'disponible', 'kilometrage')
    list_filter = ('type', 'disponible')
    search_fields = ('immatriculation', 'marque', 'modele')
    list_editable = ('disponible',)

@admin.register(Bareme)
class BaremeAdmin(admin.ModelAdmin):
    list_display = ('destination', 'fonction', 'montant_par_jour', 'date_debut', 'date_fin', 'actif')
    list_filter = ('actif', 'fonction')
    search_fields = ('destination', 'fonction')
    date_hierarchy = 'date_debut'

@admin.register(EtatDepenses)
class EtatDepensesAdmin(admin.ModelAdmin):
    list_display = ('mission', 'total_depenses', 'solde', 'valide', 'valide_par', 'date_creation')
    list_filter = ('valide',)
    search_fields = ('mission__titre', 'mission__reference')
    raw_id_fields = ('mission', 'valide_par')
    date_hierarchy = 'date_creation'

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('titre', 'destinataire', 'type', 'lue', 'date_creation')
    list_filter = ('type', 'lue')
    search_fields = ('titre', 'message', 'destinataire__username')
    raw_id_fields = ('destinataire',)
    date_hierarchy = 'date_creation'

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'action', 'model', 'object_id', 'date_action')
    list_filter = ('action', 'model')
    search_fields = ('utilisateur__username', 'model', 'object_id')
    raw_id_fields = ('utilisateur',)
    date_hierarchy = 'date_action'
    readonly_fields = ('date_action', 'ip_address')
    list_select_related = ('utilisateur',)
