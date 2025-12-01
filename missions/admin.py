from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .models import (
    Mission, MissionIntervenant, Validation,
    SignatureFinanciere, Justificatif
)
from .models_common import TypeMission, TypeFrais
from .models_vehicules import Vehicule, Bareme
from .models_documents import EtatDepenses, Notification, AuditLog
from .models_finance import Ticket, Depense
from .models_missions import (
    Budget, Delegation, HistoriqueMission,
    OrdreMission, OrdreMissionSequence,
    RapportFinal, WorkflowValidation
)

# Configuration de l'interface d'administration
@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display = ('reference', 'titre', 'type', 'statut', 'date_debut', 'date_fin')
    list_filter = ('type', 'statut')
    search_fields = ('reference', 'titre', 'description')
    date_hierarchy = 'date_creation'
    readonly_fields = ('date_creation',)
    fieldsets = (
        (None, {
            'fields': ('reference', 'titre', 'description', 'objet_mission', 'type', 'statut')
        }),
        (_('Dates'), {
            'fields': ('date_debut', 'date_fin', 'date_retour_reelle')
        }),
        (_('Lieu et transport'), {
            'fields': ('lieu_mission', 'moyen_transport', 'budget_estime')
        }),
        (_('Métadonnées'), {
            'fields': ('date_creation', 'createur')
        }),
    )

@admin.register(MissionIntervenant)
class MissionIntervenantAdmin(admin.ModelAdmin):
    list_display = ('mission', 'intervenant', 'role_dans_mission', 'date_ajout')
    list_filter = ('role_dans_mission',)
    search_fields = ('mission__titre', 'intervenant__username', 'intervenant__email')
    raw_id_fields = ('mission', 'intervenant')

@admin.register(Validation)
class ValidationAdmin(admin.ModelAdmin):
    list_display = ('mission', 'niveau', 'statut', 'valideur', 'date_creation', 'date_validation')
    list_filter = ('niveau', 'statut')
    search_fields = ('mission__titre', 'valideur__username', 'commentaire')
    readonly_fields = ('date_creation', 'date_validation')
    raw_id_fields = ('mission', 'valideur')

@admin.register(SignatureFinanciere)
class SignatureFinanciereAdmin(admin.ModelAdmin):
    list_display = ('mission', 'niveau', 'signataire', 'statut', 'date_creation', 'date_signature')
    list_filter = ('niveau', 'statut')
    search_fields = ('mission__titre', 'signataire__username')
    readonly_fields = ('date_creation', 'date_signature', 'date_derniere_relance')
    raw_id_fields = ('mission', 'signataire')

@admin.register(Justificatif)
class JustificatifAdmin(admin.ModelAdmin):
    list_display = ('mission', 'intervenant', 'type_document', 'statut', 'montant', 'date_upload')
    list_filter = ('type_document', 'statut', 'verifie')
    search_fields = ('mission__titre', 'intervenant__username', 'description')
    readonly_fields = ('date_creation', 'date_upload', 'date_verification', 'date_validation')
    raw_id_fields = ('mission', 'intervenant', 'uploader', 'verifie_par', 'valideur')
    date_hierarchy = 'date_creation'
    
    fieldsets = (
        (None, {
            'fields': ('mission', 'intervenant', 'type_document', 'categorie', 'description')
        }),
        (_('Fichier'), {
            'fields': ('fichier', 'nom_fichier', 'taille', 'hash_md5')
        }),
        (_('Validation'), {
            'fields': ('statut', 'verifie', 'verifie_par', 'date_verification', 
                      'commentaire_verification', 'valideur', 'commentaire_validation', 
                      'date_validation')
        }),
        (_('Montant'), {
            'fields': ('montant', 'devise')
        }),
        (_('Dates'), {
            'fields': ('date_creation', 'date_upload', 'date_soumission', 'date_remboursement'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.uploader_id:
            obj.uploader = request.user
        if not obj.pk:  # Only on creation
            obj.date_upload = timezone.now()
        super().save_model(request, obj, form, change)

@admin.register(TypeMission)
class TypeMissionAdmin(admin.ModelAdmin):
    list_display = ('code', 'libelle', 'description', 'actif')
    list_filter = ('actif',)
    search_fields = ('code', 'libelle', 'description')
    ordering = ('libelle',)
    list_editable = ('actif',)
    fieldsets = (
        (None, {
            'fields': ('code', 'libelle', 'description', 'actif')
        }),
    )

@admin.register(TypeFrais)
class TypeFraisAdmin(admin.ModelAdmin):
    list_display = ('code', 'libelle', 'plafond', 'remboursable', 'actif')
    list_filter = ('remboursable', 'actif')
    search_fields = ('code', 'libelle', 'description')
    ordering = ('libelle',)
    list_editable = ('plafond', 'remboursable', 'actif')
    fieldsets = (
        (None, {
            'fields': ('code', 'libelle', 'description')
        }),
        (_('Paramètres'), {
            'fields': ('plafond', 'remboursable', 'actif')
        }),
    )

# Configuration pour le modèle Depense (si disponible)
try:
    @admin.register(Depense)
    class DepenseAdmin(admin.ModelAdmin):
        list_display = ('id', 'mission', 'nature', 'montant', 'date_depense', 'date_creation')
        list_filter = ('nature', 'date_depense')
        search_fields = ('mission__titre', 'description', 'nature')
        raw_id_fields = ('mission',)
        date_hierarchy = 'date_depense'
        readonly_fields = ('date_creation',)
        
        fieldsets = (
            (None, {
                'fields': ('mission', 'nature', 'montant', 'date_depense')
            }),
            (_('Détails'), {
                'fields': ('description', 'date_creation'),
                'classes': ('collapse',)
            }),
        )
        
        def has_add_permission(self, request):
            # Désactiver l'ajout depuis l'admin
            return False
            
        def has_delete_permission(self, request, obj=None):
            # Désactiver la suppression depuis l'admin
            return False

except Exception as e:
    print(f"Warning: Le modèle Depense n'est pas disponible. Erreur: {e}")

# Configuration pour le modèle Ticket (si disponible)
try:
    @admin.register(Ticket)
    class TicketAdmin(admin.ModelAdmin):
        list_display = ('numero', 'mission', 'montant_approuve', 'statut', 'date_emission')
        list_filter = ('statut',)
        search_fields = ('numero', 'mission__titre')
        raw_id_fields = ('mission', 'emetteur')
        date_hierarchy = 'date_emission'
        
        def has_add_permission(self, request):
            # Désactiver l'ajout depuis l'admin
            return False

except Exception as e:
    print(f"Warning: Le modèle Ticket n'est pas disponible. Erreur: {e}")

# Configuration pour les modèles de mission
@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('annee', 'montant', 'date_creation')
    list_filter = ('annee',)
    search_fields = ('description',)
    readonly_fields = ('date_creation', 'date_mise_a_jour')
    ordering = ('-annee',)

@admin.register(Delegation)
class DelegationAdmin(admin.ModelAdmin):
    list_display = ('delegant', 'delegataire', 'date_debut', 'date_fin', 'active')
    list_filter = ('active', 'date_debut', 'date_fin')
    search_fields = ('delegant__username', 'delegataire__username', 'commentaire')
    raw_id_fields = ('delegant', 'delegataire')
    date_hierarchy = 'date_creation'

@admin.register(HistoriqueMission)
class HistoriqueMissionAdmin(admin.ModelAdmin):
    list_display = ('mission', 'utilisateur', 'action', 'date_action')
    list_filter = ('action',)
    search_fields = ('mission__titre', 'utilisateur__username', 'details')
    date_hierarchy = 'date_action'
    readonly_fields = ('date_action',)
    raw_id_fields = ('mission', 'utilisateur')

@admin.register(OrdreMission)
class OrdreMissionAdmin(admin.ModelAdmin):
    list_display = ('reference', 'mission', 'statut', 'date_creation', 'date_signature')
    list_filter = ('statut',)
    search_fields = ('reference', 'mission__titre')
    date_hierarchy = 'date_creation'
    raw_id_fields = ('mission', 'signataire')

@admin.register(OrdreMissionSequence)
class OrdreMissionSequenceAdmin(admin.ModelAdmin):
    list_display = ('ordre_mission', 'etape', 'signataire', 'statut', 'date_validation')
    list_filter = ('etape', 'statut')
    search_fields = ('ordre_mission__reference', 'signataire__username')
    raw_id_fields = ('ordre_mission', 'signataire')
    readonly_fields = ('date_validation',)

@admin.register(RapportFinal)
class RapportFinalAdmin(admin.ModelAdmin):
    list_display = ('mission', 'date_soumission', 'valide', 'valide_par', 'date_validation')
    list_filter = ('valide', 'date_soumission')
    search_fields = ('mission__titre', 'contenu', 'commentaires')
    date_hierarchy = 'date_soumission'
    raw_id_fields = ('mission', 'valide_par')
    readonly_fields = ('date_soumission', 'date_validation')

@admin.register(WorkflowValidation)
class WorkflowValidationAdmin(admin.ModelAdmin):
    list_display = ('type_mission', 'niveau', 'role_validation', 'actif')
    list_filter = ('type_mission', 'actif')
    search_fields = ('role_validation', 'type_mission__libelle')
    list_editable = ('actif',)
    ordering = ('type_mission', 'niveau')


@admin.register(Vehicule)
class VehiculeAdmin(admin.ModelAdmin):
    list_display = ('immatriculation', 'marque', 'modele', 'type', 'disponible', 'kilometrage')
    list_filter = ('type', 'disponible')
    search_fields = ('immatriculation', 'marque', 'modele')
    list_editable = ('disponible',)
    readonly_fields = ('date_creation',)
    date_hierarchy = 'date_acquisition'
    fieldsets = (
        (None, {
            'fields': ('immatriculation', 'marque', 'modele', 'type', 'disponible')
        }),
        (_('Informations'), {
            'fields': ('kilometrage', 'date_acquisition', 'date_assurance', 'date_visite')
        }),
        (_('Métadonnées'), {
            'fields': ('date_creation',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Bareme)
class BaremeAdmin(admin.ModelAdmin):
    list_display = ('destination', 'fonction', 'montant_par_jour', 'actif', 'date_debut', 'date_fin')
    list_filter = ('actif', 'fonction')
    search_fields = ('destination', 'fonction')
    list_editable = ('actif',)
    readonly_fields = ('date_creation',)
    date_hierarchy = 'date_debut'
    ordering = ('-date_debut', 'destination')


@admin.register(EtatDepenses)
class EtatDepensesAdmin(admin.ModelAdmin):
    list_display = ('mission', 'total_depenses', 'solde', 'valide', 'valide_par', 'date_creation')
    list_filter = ('valide', 'date_creation')
    search_fields = ('mission__titre', 'mission__reference')
    raw_id_fields = ('mission', 'valide_par')
    readonly_fields = ('date_creation', 'date_validation')
    date_hierarchy = 'date_creation'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('destinataire', 'titre', 'type', 'lue', 'date_creation')
    list_filter = ('type', 'lue', 'date_creation')
    search_fields = ('titre', 'message', 'destinataire__identifiant')
    raw_id_fields = ('destinataire',)
    readonly_fields = ('date_creation', 'date_lecture')
    date_hierarchy = 'date_creation'
    list_editable = ('lue',)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'action', 'model', 'date_action', 'ip_address')
    list_filter = ('action', 'model', 'date_action')
    search_fields = ('utilisateur__identifiant', 'model', 'object_id')
    raw_id_fields = ('utilisateur',)
    readonly_fields = ('date_action',)
    date_hierarchy = 'date_action'
    
    def has_add_permission(self, request):
        # Désactiver l'ajout depuis l'admin
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Désactiver la suppression depuis l'admin
        return False


# Les modèles JWT sont déjà enregistrés par l'application token_blacklist
# Aucun enregistrement supplémentaire nécessaire ici
