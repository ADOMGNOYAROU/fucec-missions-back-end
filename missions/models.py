from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.utils import timezone
from users.models import User

# Import des modèles supplémentaires
from .models_vehicules import Vehicule, Bareme
from .models_finance import Ticket, Avance, Depense
from .models_documents import EtatDepenses, Notification, AuditLog


class MissionStatus(models.TextChoices):
    BROUILLON = 'BROUILLON', _('Brouillon')
    EN_ATTENTE = 'EN_ATTENTE', _('En attente de validation')
    VALIDEE = 'VALIDEE', _('Validée')
    EN_COURS = 'EN_COURS', _('En cours')
    RETOUR = 'RETOUR', _('Retour déclaré')
    CLOTUREE = 'CLOTUREE', _('Clôturée')
    REJETEE = 'REJETEE', _('Rejetée')


class MissionType(models.TextChoices):
    FORMATION = 'FORMATION', _('Formation')
    REUNION = 'REUNION', _('Réunion')
    MISSION_COMMERCIALE = 'MISSION_COMMERCIALE', _('Mission commerciale')
    AUDIT = 'AUDIT', _('Audit')
    AUTRE = 'AUTRE', _('Autre')


class Mission(models.Model):
    """Modèle principal pour les missions."""

    # Informations de base
    reference = models.CharField(
        _('Référence'),
        max_length=50,
        unique=True,
        help_text=_('Référence unique de la mission')
    )

    titre = models.CharField(
        _('Titre'),
        max_length=200,
        help_text=_('Titre descriptif de la mission')
    )

    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Description détaillée de la mission')
    )

    # Type et statut
    type = models.CharField(
        max_length=20,
        choices=MissionType.choices,
        default=MissionType.AUTRE,
        verbose_name=_('Type de mission')
    )

    statut = models.CharField(
        max_length=15,
        choices=MissionStatus.choices,
        default=MissionStatus.BROUILLON,
        verbose_name=_('Statut')
    )

    # Dates
    date_debut = models.DateField(
        _('Date de début'),
        help_text=_('Date de début de la mission')
    )

    date_fin = models.DateField(
        _('Date de fin'),
        help_text=_('Date de fin de la mission')
    )

    date_retour_reelle = models.DateField(
        _('Date de retour réelle'),
        null=True,
        blank=True,
        help_text=_('Date réelle de retour')
    )

    # Lieu
    lieu_mission = models.CharField(
        _('Lieu de mission'),
        max_length=200,
        help_text=_('Lieu où se déroule la mission')
    )

    # Budget et avances
    budget_estime = models.DecimalField(
        _('Budget estimé'),
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('Budget estimé pour la mission en FCFA')
    )

    avance_demandee = models.DecimalField(
        _('Avance demandée'),
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('Montant d\'avance demandé en FCFA')
    )

    avance_versee = models.BooleanField(
        _('Avance versée'),
        default=False,
        help_text=_('L\'avance a-t-elle été versée ?')
    )

    # Relations
    createur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='missions_creees',
        verbose_name=_('Créateur')
    )

    entite = models.ForeignKey(
        'users.Entite',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='missions',
        verbose_name=_('Entité')
    )

    # Participants (maintenu pour compatibilité)
    participants = models.ManyToManyField(
        User,
        related_name='missions_participees',
        verbose_name=_('Participants'),
        blank=True
    )

    # Véhicule et chauffeur
    vehicule = models.ForeignKey(
        'Vehicule',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='missions',
        verbose_name=_('Véhicule')
    )

    chauffeur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='missions_conduites',
        verbose_name=_('Chauffeur')
    )

    # Métadonnées
    signatures_completes = models.BooleanField(
        _('Signatures complètes'),
        default=False,
        help_text=_('Toutes les signatures financières sont-elles complètes ?')
    )

    # Workflow de retour de mission
    date_debut_reelle = models.DateTimeField(
        _('Date de début réelle'),
        null=True,
        blank=True,
        help_text=_('Date réelle de début de la mission')
    )

    date_retour_reelle = models.DateTimeField(
        _('Date de retour réelle'),
        null=True,
        blank=True,
        help_text=_('Date réelle de retour de mission déclarée par l\'agent')
    )

    retour_declare = models.BooleanField(
        _('Retour déclaré'),
        default=False,
        help_text=_('L\'agent a-t-il déclaré son retour ?')
    )

    date_limite_justificatifs = models.DateTimeField(
        _('Date limite justificatifs'),
        null=True,
        blank=True,
        help_text=_('Date limite pour déposer les justificatifs (72h après retour)')
    )

    justificatifs_deposes = models.BooleanField(
        _('Justificatifs déposés'),
        default=False,
        help_text=_('Tous les justificatifs ont-ils été déposés ?')
    )

    justificatifs_verifies = models.BooleanField(
        _('Justificatifs vérifiés'),
        default=False,
        help_text=_('Les justificatifs ont-ils été vérifiés par RH ?')
    )

    relance_justificatifs = models.BooleanField(
        _('Relance justificatifs'),
        default=False,
        help_text=_('Une relance pour les justificatifs a-t-elle été effectuée ?')
    )

    date_derniere_relance_justificatifs = models.DateTimeField(
        _('Date dernière relance justificatifs'),
        null=True,
        blank=True
    )

    # Clôture et archivage
    solde_calcule = models.DecimalField(
        _('Solde calculé'),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_('Solde final calculé (positif = FUCEC doit rembourser, négatif = agent doit rembourser)')
    )

    cloturee = models.BooleanField(
        _('Clôturée'),
        default=False,
        help_text=_('La mission est-elle clôturée ?')
    )

    date_cloture = models.DateTimeField(
        _('Date de clôture'),
        null=True,
        blank=True
    )

    archivee = models.BooleanField(
        _('Archivée'),
        default=False,
        help_text=_('La mission est-elle archivée ?')
    )

    date_archivage = models.DateTimeField(
        _('Date d\'archivage'),
        null=True,
        blank=True
    )

    date_creation = models.DateTimeField(
        _('Date de création'),
        auto_now_add=True
    )

    class Meta:
        verbose_name = _('Mission')
        verbose_name_plural = _('Missions')
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.reference} - {self.titre}"

    @property
    def duree(self):
        """Calcule la durée de la mission en jours."""
        if self.date_fin and self.date_debut:
            return (self.date_fin - self.date_debut).days + 1
        return 0

    @property
    def nombre_participants(self):
        """Nombre de participants."""
        return self.participants.count()

    def save(self, *args, **kwargs):
        """Génère automatiquement une référence si elle n'existe pas."""
        if not self.reference:
            # Génère une référence basée sur la date et un compteur
            from django.utils import timezone
            today = timezone.now().date()
            count = Mission.objects.filter(date_creation__date=today).count() + 1
            self.reference = f"MIS-{today.strftime('%Y%m%d')}-{count:03d}"
        super().save(*args, **kwargs)


class MissionIntervenant(models.Model):
    """Table de liaison entre Mission et User (intervenants)."""

    mission = models.ForeignKey(
        Mission,
        on_delete=models.CASCADE,
        verbose_name=_('Mission')
    )

    intervenant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('Intervenant')
    )

    role_dans_mission = models.CharField(
        _('Rôle dans la mission'),
        max_length=100,
        blank=True,
        help_text=_('Rôle spécifique de l\'intervenant dans cette mission')
    )

    date_ajout = models.DateTimeField(
        _('Date d\'ajout'),
        auto_now_add=True
    )

    class Meta:
        verbose_name = _('Intervenant de mission')
        verbose_name_plural = _('Intervenants de mission')
        unique_together = ['mission', 'intervenant']

    def __str__(self):
        return f"{self.intervenant.get_full_name()} - {self.mission.titre}"


class ValidationStatus(models.TextChoices):
    EN_ATTENTE = 'EN_ATTENTE', _('En attente')
    VALIDEE = 'VALIDEE', _('Validée')
    REJETEE = 'REJETEE', _('Rejetée')
    REPORTEE = 'REPORTEE', _('Reportée')


class ValidationNiveau(models.TextChoices):
    N_PLUS_1 = 'N_PLUS_1', _('N+1 (Chef direct)')
    N_PLUS_2 = 'N_PLUS_2', _('N+2 (Chef du N+1)')
    DGA_DG = 'DGA_DG', _('DGA/DG (Direction)')


class SignatureFinanciere(models.Model):
    """Modèle pour les signatures financières."""

    STATUTS = [
        ('EN_ATTENTE', _('En attente')),
        ('SIGNE', _('Signé')),
        ('REFUSE', _('Refusé')),
    ]

    NIVEAUX = [
        ('AGENT', _('Agent')),
        ('CHEF_AGENCE', _('Chef d\'agence')),
        ('DIRECTEUR_FINANCES', _('Directeur Finances')),
        ('COMPTABLE', _('Comptable')),
        ('DG', _('Directeur Général')),
    ]

    mission = models.ForeignKey(
        Mission,
        on_delete=models.CASCADE,
        related_name='signatures_financieres',
        verbose_name=_('Mission')
    )

    niveau = models.CharField(
        _('Niveau'),
        max_length=20,
        choices=NIVEAUX,
        help_text=_('Niveau de signature requis')
    )

    signataire = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='signatures_financieres',
        verbose_name=_('Signataire')
    )

    date_signature = models.DateTimeField(
        _('Date de signature'),
        null=True,
        blank=True
    )

    ordre = models.PositiveIntegerField(
        _('Ordre'),
        default=1,
        help_text=_('Ordre dans le processus de signature')
    )

    statut = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUTS,
        default='EN_ATTENTE',
        help_text=_('Statut de la signature')
    )

    commentaire = models.TextField(
        _('Commentaire'),
        blank=True,
        help_text=_('Commentaire du signataire')
    )

    date_creation = models.DateTimeField(
        _('Date de création'),
        auto_now_add=True
    )

    # Timers et relances
    date_limite_signature = models.DateTimeField(
        _('Date limite de signature'),
        null=True,
        blank=True,
        help_text=_('Date et heure limite pour la signature (72h)')
    )

    relance_effectuee = models.BooleanField(
        _('Relance effectuée'),
        default=False,
        help_text=_('Une relance automatique a-t-elle été envoyée ?')
    )

    date_derniere_relance = models.DateTimeField(
        _('Date de dernière relance'),
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _('Signature financière')
        verbose_name_plural = _('Signatures financières')
        ordering = ['mission', 'ordre']
        unique_together = ['mission', 'niveau']

    def __str__(self):
        return f"Signature {self.niveau} - {self.mission.titre}"


class Validation(models.Model):
    """Modèle pour les validations de mission."""

    mission = models.ForeignKey(
        Mission,
        on_delete=models.CASCADE,
        related_name='validations',
        verbose_name=_('Mission')
    )

    valideur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='validations_effectuees',
        verbose_name=_('Validateur')
    )

    niveau = models.CharField(
        max_length=20,
        choices=ValidationNiveau.choices,
        verbose_name=_('Niveau de validation')
    )

    statut = models.CharField(
        max_length=10,
        choices=ValidationStatus.choices,
        default=ValidationStatus.EN_ATTENTE,
        verbose_name=_('Statut')
    )

    commentaire = models.TextField(
        _('Commentaire'),
        blank=True,
        help_text=_('Commentaire du valideur')
    )

    # Dates
    date_creation = models.DateTimeField(
        _('Date de création'),
        auto_now_add=True
    )

    date_validation = models.DateTimeField(
        _('Date de validation'),
        null=True,
        blank=True
    )

    # Métadonnées
    ordre = models.PositiveIntegerField(
        _('Ordre de validation'),
        default=1,
        help_text=_('Ordre dans le processus de validation')
    )

    delai_heures = models.PositiveIntegerField(
        _('Délai en heures'),
        default=24,
        help_text=_('Délai imparti pour la validation en heures')
    )

    date_echeance = models.DateTimeField(
        _('Date d\'échéance'),
        null=True,
        blank=True,
        help_text=_('Date et heure limite pour la validation')
    )

    est_actif = models.BooleanField(
        _('Validation active'),
        default=True,
        help_text=_('Indique si cette validation est toujours active')
    )

    class Meta:
        verbose_name = _('Validation')
        verbose_name_plural = _('Validations')
        ordering = ['mission', 'ordre']
        unique_together = ['mission', 'valideur', 'niveau']

    def __str__(self):
        return f"Validation {self.mission.titre} - {self.valideur.get_full_name()} ({self.niveau})"

    @property
    def en_retard(self):
        """Vérifie si la validation est en retard."""
        if self.date_echeance:
            from django.utils import timezone
            return timezone.now() > self.date_echeance
        # Fallback : en retard si créée il y a plus de delai_heures
        from django.utils import timezone
        return (timezone.now() - self.date_creation).seconds > (self.delai_heures * 3600)


class JustificatifType(models.TextChoices):
    TRANSPORT = 'TRANSPORT', _('Transport')
    HEBERGEMENT = 'HEBERGEMENT', _('Hébergement')
    RESTAURATION = 'RESTAURATION', _('Restauration')
    AUTRE = 'AUTRE', _('Autre')


class JustificatifStatus(models.TextChoices):
    EN_ATTENTE = 'EN_ATTENTE', _('En attente')
    VALIDE = 'VALIDE', _('Validé')
    REJETE = 'REJETE', _('Rejeté')
    REMBOURSE = 'REMBOURSE', _('Remboursé')


class Justificatif(models.Model):
    """Modèle pour les justificatifs de mission."""

    mission = models.ForeignKey(
        Mission,
        on_delete=models.CASCADE,
        related_name='justificatifs',
        verbose_name=_('Mission')
    )

    intervenant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='justificatifs',
        verbose_name=_('Intervenant')
    )

    # Informations du justificatif
    type_document = models.CharField(
        _('Type de document'),
        max_length=50,
        default='JUSTIFICATIF',
        help_text=_('Type de document justificatif')
    )

    categorie = models.CharField(
        _('Catégorie'),
        max_length=100,
        blank=True,
        help_text=_('Catégorie détaillée du justificatif')
    )

    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Description détaillée du justificatif')
    )

    # Fichier joint
    fichier = models.FileField(
        _('Fichier'),
        upload_to='justificatifs/%Y/%m/',
        blank=True,
        null=True,
        help_text=_('Justificatif scanné ou photo')
    )

    nom_fichier = models.CharField(
        _('Nom du fichier'),
        max_length=255,
        blank=True,
        help_text=_('Nom original du fichier téléchargé')
    )

    taille = models.BigIntegerField(
        _('Taille'),
        default=0,
        help_text=_('Taille du fichier en octets')
    )

    hash_md5 = models.CharField(
        _('Hash MD5'),
        max_length=32,
        blank=True,
        help_text=_('Hash MD5 du fichier pour vérification d\'intégrité')
    )

    uploader = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='justificatifs_uploades',
        verbose_name=_('Uploader')
    )

    date_upload = models.DateTimeField(
        _('Date d\'upload'),
        default=timezone.now
    )

    # Vérification
    verifie = models.BooleanField(
        _('Vérifié'),
        default=False,
        help_text=_('Le justificatif a-t-il été vérifié ?')
    )

    verifie_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='justificatifs_verifies',
        verbose_name=_('Vérifié par')
    )

    date_verification = models.DateTimeField(
        _('Date de vérification'),
        null=True,
        blank=True
    )

    commentaire_verification = models.TextField(
        _('Commentaire de vérification'),
        blank=True
    )

    # Montant et devise (gardé pour compatibilité)
    montant = models.DecimalField(
        _('Montant'),
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('Montant en FCFA')
    )

    devise = models.CharField(
        _('Devise'),
        max_length=3,
        default='XAF',
        help_text=_('Code devise ISO (XAF pour FCFA)')
    )

    # Statut et validation
    statut = models.CharField(
        max_length=10,
        choices=JustificatifStatus.choices,
        default=JustificatifStatus.EN_ATTENTE,
        verbose_name=_('Statut')
    )

    # Validation
    valideur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='justificatifs_valides',
        verbose_name=_('Validateur')
    )

    commentaire_validation = models.TextField(
        _('Commentaire de validation'),
        blank=True
    )

    # Dates
    date_creation = models.DateTimeField(
        _('Date de création'),
        auto_now_add=True
    )

    date_soumission = models.DateTimeField(
        _('Date de soumission'),
        null=True,
        blank=True
    )

    date_validation = models.DateTimeField(
        _('Date de validation'),
        null=True,
        blank=True
    )

    date_remboursement = models.DateTimeField(
        _('Date de remboursement'),
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _('Justificatif')
        verbose_name_plural = _('Justificatifs')
        ordering = ['-date_creation']

    def __str__(self):
        return f"Justificatif {self.mission.titre} - {self.intervenant.get_full_name()} - {self.montant} {self.devise}"

    @property
    def montant_formate(self):
        """Retourne le montant formaté."""
        return f"{self.montant:,.0f} {self.devise}"

    def peut_etre_valide_par(self, user):
        """Vérifie si l'utilisateur peut valider ce justificatif."""
        if not user.can_validate:
            return False

        # Les validateurs peuvent valider les justificatifs de leur équipe
        if user.role == 'CHEF_AGENCE':
            return self.intervenant.manager == user or self.intervenant in user.get_subordinates()
        elif user.role in ['RESPONSABLE_COPEC', 'DG', 'RH', 'COMPTABLE']:
            return True

        return False