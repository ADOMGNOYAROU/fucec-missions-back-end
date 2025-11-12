from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import (
    Mission, Validation, Justificatif, MissionIntervenant,
    SignatureFinanciere, Ticket, Avance, Depense, EtatDepenses, Notification
)


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
            'id', 'reference', 'titre', 'description', 'type', 'statut',
            'date_debut', 'date_fin', 'lieu_mission', 'budget_estime', 'avance_demandee',
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
            'titre', 'description', 'type',
            'date_debut', 'date_fin', 'lieu_mission', 'budget_estime', 'avance_demandee',
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
