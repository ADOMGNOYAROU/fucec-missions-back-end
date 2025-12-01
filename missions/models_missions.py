from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from .models_common import TypeMission

class Budget(models.Model):
    """Modèle pour les budgets de mission."""
    annee = models.PositiveIntegerField(_('Année'), unique=True)
    montant = models.DecimalField(_('Montant alloué'), max_digits=12, decimal_places=2)
    description = models.TextField(_('Description'), blank=True)
    date_creation = models.DateTimeField(_('Date de création'), auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(_('Dernière mise à jour'), auto_now=True)

    class Meta:
        verbose_name = _('Budget')
        verbose_name_plural = _('Budgets')
        ordering = ['-annee']

    def __str__(self):
        return f"Budget {self.annee} - {self.montant}"


class Delegation(models.Model):
    """Modèle pour les délégations de signature."""
    delegant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='delegations_donnes',
        verbose_name=_('Délégant')
    )
    delegataire = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='delegations_recues',
        verbose_name=_('Délégaire')
    )
    date_debut = models.DateField(_('Date de début'))
    date_fin = models.DateField(_('Date de fin'))
    active = models.BooleanField(_('Active'), default=True)
    commentaire = models.TextField(_('Commentaire'), blank=True)
    date_creation = models.DateTimeField(_('Date de création'), auto_now_add=True)

    class Meta:
        verbose_name = _('Délégation')
        verbose_name_plural = _('Délégations')
        ordering = ['-date_creation']

    def __str__(self):
        return f"Délégation de {self.delegant} à {self.delegataire}"


class HistoriqueMission(models.Model):
    """Modèle pour l'historique des actions sur les missions."""
    mission = models.ForeignKey('Mission', on_delete=models.CASCADE, verbose_name=_('Mission'))
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('Utilisateur')
    )
    action = models.CharField(_('Action'), max_length=100)
    details = models.JSONField(_('Détails'), default=dict, blank=True)
    date_action = models.DateTimeField(_('Date'), auto_now_add=True)

    class Meta:
        verbose_name = _('Entrée historique')
        verbose_name_plural = _('Historique des missions')
        ordering = ['-date_action']

    def __str__(self):
        return f"{self.mission} - {self.action} par {self.utilisateur}"


class OrdreMission(models.Model):
    """Modèle pour les ordres de mission."""
    reference = models.CharField(_('Référence'), max_length=50, unique=True)
    mission = models.OneToOneField(
        'Mission',
        on_delete=models.CASCADE,
        related_name='ordre_mission',
        verbose_name=_('Mission')
    )
    date_creation = models.DateTimeField(_('Date de création'), auto_now_add=True)
    date_signature = models.DateTimeField(_('Date de signature'), null=True, blank=True)
    signataire = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='ordres_signes',
        verbose_name=_('Signataire')
    )
    statut = models.CharField(_('Statut'), max_length=20, default='BROUILLON')

    class Meta:
        verbose_name = _('Ordre de mission')
        verbose_name_plural = _('Ordres de mission')
        ordering = ['-date_creation']

    def __str__(self):
        return f"Ordre de mission {self.reference}"


class OrdreMissionSequence(models.Model):
    """Séquence de validation pour un ordre de mission."""
    ordre_mission = models.ForeignKey(
        OrdreMission,
        on_delete=models.CASCADE,
        related_name='sequences_validation',
        verbose_name=_('Ordre de mission')
    )
    etape = models.PositiveIntegerField(_('Étape'))
    signataire = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_('Signataire')
    )
    statut = models.CharField(_('Statut'), max_length=20, default='EN_ATTENTE')
    date_validation = models.DateTimeField(_('Date de validation'), null=True, blank=True)
    commentaire = models.TextField(_('Commentaire'), blank=True)

    class Meta:
        verbose_name = _('Séquence de validation')
        verbose_name_plural = _('Séquences de validation')
        ordering = ['ordre_mission', 'etape']
        unique_together = ('ordre_mission', 'etape')

    def __str__(self):
        return f"Validation {self.etape} - {self.ordre_mission}"


class RapportFinal(models.Model):
    """Modèle pour les rapports finaux de mission."""
    mission = models.OneToOneField(
        'Mission',
        on_delete=models.CASCADE,
        related_name='rapport_final',
        verbose_name=_('Mission')
    )
    contenu = models.TextField(_('Contenu'))
    date_soumission = models.DateTimeField(_('Date de soumission'), auto_now_add=True)
    valide = models.BooleanField(_('Validé'), default=False)
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rapports_valides',
        verbose_name=_('Validé par')
    )
    date_validation = models.DateTimeField(_('Date de validation'), null=True, blank=True)
    commentaires = models.TextField(_('Commentaires'), blank=True)

    class Meta:
        verbose_name = _('Rapport final')
        verbose_name_plural = _('Rapports finaux')
        ordering = ['-date_soumission']

    def __str__(self):
        return f"Rapport final - {self.mission}"


class WorkflowValidation(models.Model):
    """Configuration des workflows de validation par type de mission."""
    type_mission = models.ForeignKey(
        TypeMission,
        on_delete=models.CASCADE,
        related_name='workflows_validation',
        verbose_name=_('Type de mission')
    )
    niveau = models.PositiveIntegerField(_('Niveau'))
    role_validation = models.CharField(_('Rôle de validation'), max_length=100)
    actif = models.BooleanField(_('Actif'), default=True)
    date_creation = models.DateTimeField(_('Date de création'), auto_now_add=True)

    class Meta:
        verbose_name = _('Étape de validation')
        verbose_name_plural = _('Workflow de validation')
        ordering = ['type_mission', 'niveau']
        unique_together = ('type_mission', 'niveau')

    def __str__(self):
        return f"{self.type_mission} - Niveau {self.niveau}: {self.role_validation}"
