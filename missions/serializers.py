from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import (
    Mission, Validation, Justificatif, MissionIntervenant,
    SignatureFinanciere, Ticket, Avance, Depense, EtatDepenses, Notification
)
from .models_common import TypeMission, TypeFrais
from .models_missions import Budget, Delegation, HistoriqueMission, OrdreMission, RapportFinal, WorkflowValidation
from .models_vehicules import Vehicule, Bareme
from users.models import User, Entite, Service, UserRole


class MissionIntervenantSerializer(serializers.ModelSerializer):
    """Serializer pour les intervenants de mission."""

    intervenant_nom = serializers.CharField(source='intervenant.get_full_name', read_only=True)
    intervenant_role = serializers.CharField(source='intervenant.role', read_only=True)

    class Meta:
        model = MissionIntervenant
        fields = [
            'id', 'intervenant', 'intervenant_nom', 'intervenant_role',
            'role_dans_mission', 'date_ajout'
        ]
        read_only_fields = ['id', 'date_ajout']


class MissionSerializer(serializers.ModelSerializer):
    """Serializer pour les missions."""

    createur_nom = serializers.CharField(source='createur.get_full_name', read_only=True)
    intervenants_details = MissionIntervenantSerializer(source='missionintervenant_set', many=True, read_only=True)
    intervenants_count = serializers.SerializerMethodField()
    duree = serializers.SerializerMethodField()
    can_be_validated_by_current_user = serializers.SerializerMethodField()

    class Meta:
        model = Mission
        fields = [
            'id', 'reference', 'titre', 'description', 'objet_mission', 'type', 'statut',
            'date_debut', 'date_fin', 'lieu_mission', 'moyen_transport', 'budget_estime', 'avance_demandee',
            'createur', 'createur_nom', 'participants',
            'intervenants_details', 'intervenants_count', 'duree',
            'date_creation',
            'can_be_validated_by_current_user'
        ]
        read_only_fields = ['id', 'date_creation']

    def get_intervenants_count(self, obj):
        return obj.intervenants_count

    def get_duree(self, obj):
        return obj.duree

    def get_can_be_validated_by_current_user(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.can_be_validated_by(request.user)
        return False

    def create(self, validated_data):
        intervenants = validated_data.pop('intervenants', [])
        validated_data['createur'] = self.context['request'].user
        mission = super().create(validated_data)

        # Ajouter les intervenants
        for intervenant in intervenants:
            MissionIntervenant.objects.create(
                mission=mission,
                intervenant=intervenant
            )

        return mission

    def update(self, instance, validated_data):
        intervenants = validated_data.pop('intervenants', None)
        mission = super().update(instance, validated_data)

        if intervenants is not None:
            # Supprimer les anciens intervenants
            MissionIntervenant.objects.filter(mission=mission).delete()
            # Ajouter les nouveaux
            for intervenant in intervenants:
                MissionIntervenant.objects.create(
                    mission=mission,
                    intervenant=intervenant
                )

        return mission


class MissionCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création de missions - retourne le serializer complet."""

    class Meta:
        model = Mission
        fields = [
            'titre', 'description', 'objet_mission', 'type',
            'date_debut', 'date_fin', 'lieu_mission', 'moyen_transport', 'budget_estime', 'avance_demandee',
            'participants'
        ]

    def create(self, validated_data):
        participants = validated_data.pop('participants', [])
        validated_data['createur'] = self.context['request'].user
        mission = super().create(validated_data)

        # Ajouter les participants
        if participants:
            mission.participants.set(participants)

        return mission


class ValidationSerializer(serializers.ModelSerializer):
    """Serializer pour les validations."""

    valideur_nom = serializers.CharField(source='valideur.get_full_name', read_only=True)
    mission_titre = serializers.CharField(source='mission.titre', read_only=True)

    class Meta:
        model = Validation
        fields = [
            'id', 'mission', 'mission_titre', 'valideur', 'valideur_nom',
            'niveau', 'statut', 'commentaire', 'ordre',
            'date_creation', 'date_validation', 'en_retard'
        ]
        read_only_fields = ['id', 'date_creation', 'en_retard']

    def validate(self, data):
        # Vérifier que l'utilisateur peut valider cette mission
        request = self.context.get('request')
        if request and request.user:
            mission = data.get('mission')
            if mission and not mission.can_be_validated_by(request.user):
                raise serializers.ValidationError(
                    _("Vous n'êtes pas autorisé à valider cette mission.")
                )
        return data


class JustificatifSerializer(serializers.ModelSerializer):
    """Serializer pour les justificatifs."""

    intervenant_nom = serializers.CharField(source='intervenant.get_full_name', read_only=True)
    mission_titre = serializers.CharField(source='mission.titre', read_only=True)
    montant_formate = serializers.SerializerMethodField()

    class Meta:
        model = Justificatif
        fields = [
            'id', 'mission', 'mission_titre', 'intervenant', 'intervenant_nom',
            'type', 'categorie', 'description', 'montant', 'montant_formate', 'devise',
            'statut', 'fichier', 'nom_fichier',
            'valideur', 'commentaire_validation',
            'date_creation', 'date_soumission', 'date_validation', 'date_remboursement'
        ]
        read_only_fields = ['id', 'date_creation', 'montant_formate']

    def get_montant_formate(self, obj):
        return obj.montant_formate

    def validate(self, data):
        # Vérifier que l'utilisateur peut créer des justificatifs pour cette mission
        request = self.context.get('request')
        if request and request.user:
            intervenant = data.get('intervenant')
            if intervenant != request.user:
                # Seuls les intervenants peuvent créer leurs propres justificatifs
                raise serializers.ValidationError(
                    _("Vous ne pouvez créer des justificatifs que pour vous-même.")
                )
        return data


class JustificatifValidationSerializer(serializers.ModelSerializer):
    """Serializer pour la validation des justificatifs."""

    intervenant_nom = serializers.CharField(source='intervenant.get_full_name', read_only=True)
    mission_titre = serializers.CharField(source='mission.titre', read_only=True)

    class Meta:
        model = Justificatif
        fields = [
            'id', 'mission', 'mission_titre', 'intervenant', 'intervenant_nom',
            'type', 'categorie', 'description', 'montant', 'devise',
            'statut', 'commentaire_validation'
        ]

    def validate(self, data):
        # Vérifier que l'utilisateur peut valider ce justificatif
        request = self.context.get('request')
        if request and request.user:
            justificatif = self.instance
            if justificatif and not justificatif.peut_etre_valide_par(request.user):
                raise serializers.ValidationError(
                    _("Vous n'êtes pas autorisé à valider ce justificatif.")
                )
        return data


class SignatureFinanciereSerializer(serializers.ModelSerializer):
    """Serializer pour les signatures financières."""

    signataire_nom = serializers.CharField(source='signataire.get_full_name', read_only=True)
    mission_titre = serializers.CharField(source='mission.titre', read_only=True)

    class Meta:
        model = SignatureFinanciere
        fields = [
            'id', 'mission', 'mission_titre', 'niveau', 'signataire', 'signataire_nom',
            'date_signature', 'ordre', 'statut', 'commentaire', 'date_creation'
        ]
        read_only_fields = ['id', 'date_creation']


class TicketSerializer(serializers.ModelSerializer):
    """Serializer pour les tickets financiers."""

    emetteur_nom = serializers.CharField(source='emetteur.get_full_name', read_only=True)
    mission_titre = serializers.CharField(source='mission.titre', read_only=True)

    class Meta:
        model = Ticket
        fields = [
            'id', 'numero', 'mission', 'mission_titre', 'montant_approuve',
            'date_emission', 'emetteur', 'emetteur_nom', 'statut', 'date_creation'
        ]
        read_only_fields = ['id', 'date_creation']


class AvanceSerializer(serializers.ModelSerializer):
    """Serializer pour les avances."""

    verse_par_nom = serializers.CharField(source='verse_par.get_full_name', read_only=True)
    beneficiaire_nom = serializers.CharField(source='beneficiaire.get_full_name', read_only=True)
    mission_titre = serializers.CharField(source='mission.titre', read_only=True)

    class Meta:
        model = Avance
        fields = [
            'id', 'mission', 'mission_titre', 'montant', 'date_versement',
            'verse_par', 'verse_par_nom', 'beneficiaire', 'beneficiaire_nom',
            'statut', 'mode_versement', 'date_creation'
        ]
        read_only_fields = ['id', 'date_creation']


class DepenseSerializer(serializers.ModelSerializer):
    """Serializer pour les dépenses."""

    mission_titre = serializers.CharField(source='mission.titre', read_only=True)

    class Meta:
        model = Depense
        fields = [
            'id', 'mission', 'mission_titre', 'nature', 'montant',
            'date_depense', 'description', 'date_creation'
        ]
        read_only_fields = ['id', 'date_creation']


class EtatDepensesSerializer(serializers.ModelSerializer):
    """Serializer pour les états des dépenses."""

    mission_titre = serializers.CharField(source='mission.titre', read_only=True)
    valide_par_nom = serializers.CharField(source='valide_par.get_full_name', read_only=True)

    class Meta:
        model = EtatDepenses
        fields = [
            'id', 'mission', 'mission_titre', 'fichier', 'total_depenses',
            'solde', 'valide', 'valide_par', 'valide_par_nom', 'date_validation',
            'date_creation'
        ]
        read_only_fields = ['id', 'date_creation']


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer pour les notifications."""

    class Meta:
        model = Notification
        fields = [
            'id', 'titre', 'message', 'type', 'lue', 'date_creation',
            'date_lecture', 'lien'
        ]
        read_only_fields = ['id', 'date_creation', 'date_lecture']


class AvanceCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer des avances."""

    class Meta:
        model = Avance
        fields = [
            'mission', 'montant', 'beneficiaire', 'mode_versement'
        ]

    def validate_montant(self, value):
        """Valider que le montant ne dépasse pas l'avance demandée"""
        mission = self.initial_data.get('mission')
        if mission:
            try:
                mission_obj = Mission.objects.get(id=mission)
                if value > mission_obj.avance_demandee:
                    raise serializers.ValidationError(
                        f"Le montant ne peut pas dépasser l'avance demandée ({mission_obj.avance_demandee} FCFA)"
                    )
            except Mission.DoesNotExist:
                pass
        return value


# ========== NOUVEAUX SERIALIZERS POUR LES MODÈLES COMPLÉMENTAIRES ==========

class ServiceSerializer(serializers.ModelSerializer):
    """Serializer pour les services/départements."""
    chef_nom = serializers.CharField(source='chef.get_full_name', read_only=True)
    nombre_employes = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = [
            'id', 'code', 'nom', 'description', 'chef', 'chef_nom',
            'budget_annuel', 'actif', 'nombre_employes', 'date_creation'
        ]
        read_only_fields = ['id', 'date_creation']

    def get_nombre_employes(self, obj):
        return obj.employes.count() if hasattr(obj, 'employes') else 0


class BudgetSerializer(serializers.ModelSerializer):
    """Serializer pour les budgets annuels."""

    class Meta:
        model = Budget
        fields = [
            'id', 'annee', 'montant', 'description',
            'date_creation', 'date_mise_a_jour'
        ]
        read_only_fields = ['id', 'date_creation', 'date_mise_a_jour']


class DelegationSerializer(serializers.ModelSerializer):
    """Serializer pour les délégations de pouvoir."""
    delegant_nom = serializers.CharField(source='delegant.get_full_name', read_only=True)
    delegataire_nom = serializers.CharField(source='delegataire.get_full_name', read_only=True)
    est_active = serializers.SerializerMethodField()

    class Meta:
        model = Delegation
        fields = [
            'id', 'delegant', 'delegant_nom', 'delegataire', 'delegataire_nom',
            'date_debut', 'date_fin', 'active', 'est_active', 'commentaire', 'date_creation'
        ]
        read_only_fields = ['id', 'date_creation']

    def get_est_active(self, obj):
        """Vérifie si la délégation est actuellement active."""
        from django.utils import timezone
        now = timezone.now().date()
        return obj.active and obj.date_debut <= now <= obj.date_fin


class RapportFinalSerializer(serializers.ModelSerializer):
    """Serializer pour les rapports finaux de mission."""
    mission_titre = serializers.CharField(source='mission.titre', read_only=True)
    valide_par_nom = serializers.CharField(source='valide_par.get_full_name', read_only=True)

    class Meta:
        model = RapportFinal
        fields = [
            'id', 'mission', 'mission_titre', 'contenu', 'date_soumission',
            'valide', 'valide_par', 'valide_par_nom', 'date_validation', 'commentaires'
        ]
        read_only_fields = ['id', 'date_soumission']


class HistoriqueMissionSerializer(serializers.ModelSerializer):
    """Serializer pour l'historique des missions."""
    utilisateur_nom = serializers.CharField(source='utilisateur.get_full_name', read_only=True)
    mission_titre = serializers.CharField(source='mission.titre', read_only=True)

    class Meta:
        model = HistoriqueMission
        fields = [
            'id', 'mission', 'mission_titre', 'utilisateur', 'utilisateur_nom',
            'action', 'details', 'date_action'
        ]
        read_only_fields = ['id', 'date_action']


class WorkflowValidationSerializer(serializers.ModelSerializer):
    """Serializer pour les étapes de validation configurables."""
    type_mission_libelle = serializers.CharField(source='type_mission.libelle', read_only=True)

    class Meta:
        model = WorkflowValidation
        fields = [
            'id', 'type_mission', 'type_mission_libelle', 'niveau',
            'role_validation', 'actif', 'date_creation'
        ]
        read_only_fields = ['id', 'date_creation']


class TypeMissionSerializer(serializers.ModelSerializer):
    """Serializer pour les types de mission."""

    class Meta:
        model = TypeMission
        fields = ['id', 'code', 'libelle', 'description', 'actif']
        read_only_fields = ['id']


class TypeFraisSerializer(serializers.ModelSerializer):
    """Serializer pour les types de frais."""

    class Meta:
        model = TypeFrais
        fields = [
            'id', 'code', 'libelle', 'description',
            'plafond', 'remboursable', 'actif'
        ]
        read_only_fields = ['id']


class VehiculeSerializer(serializers.ModelSerializer):
    """Serializer pour les véhicules."""

    class Meta:
        model = Vehicule
        fields = [
            'id', 'immatriculation', 'marque', 'modele', 'type',
            'disponible', 'kilometrage', 'date_acquisition', 'date_assurance', 'date_visite', 'date_creation'
        ]
        read_only_fields = ['id', 'date_creation']


class BaremeSerializer(serializers.ModelSerializer):
    """Serializer pour les barèmes kilométriques."""

    class Meta:
        model = Bareme
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    """Serializer pour les utilisateurs, utilisé notamment pour les chauffeurs."""
    full_name = serializers.SerializerMethodField()
    role_display = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'identifiant', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'role_display', 'telephone', 'is_active', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_role_display(self, obj):
        return dict(UserRole.choices).get(obj.role, obj.role)
