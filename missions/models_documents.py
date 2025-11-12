from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import User


class EtatDepenses(models.Model):
    """Modèle pour les états des dépenses."""

    mission = models.OneToOneField(
        'Mission',
        on_delete=models.CASCADE,
        related_name='etat_depenses',
        verbose_name=_('Mission')
    )

    fichier = models.FileField(
        _('Fichier'),
        upload_to='etats_depenses/',
        help_text=_('Fichier PDF de l\'état des dépenses')
    )

    total_depenses = models.DecimalField(
        _('Total des dépenses'),
        max_digits=12,
        decimal_places=2,
        help_text=_('Total des dépenses en FCFA')
    )

    solde = models.DecimalField(
        _('Solde'),
        max_digits=12,
        decimal_places=2,
        help_text=_('Solde restant en FCFA')
    )

    valide = models.BooleanField(
        _('Validé'),
        default=False,
        help_text=_('L\'état des dépenses est-il validé ?')
    )

    valide_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='etats_depenses_valides',
        verbose_name=_('Validé par')
    )

    date_validation = models.DateTimeField(
        _('Date de validation'),
        null=True,
        blank=True
    )

    date_creation = models.DateTimeField(
        _('Date de création'),
        auto_now_add=True
    )

    class Meta:
        verbose_name = _('État des dépenses')
        verbose_name_plural = _('États des dépenses')
        ordering = ['-date_creation']

    def __str__(self):
        return f"État dépenses - {self.mission.titre}"


class Notification(models.Model):
    """Modèle pour les notifications utilisateur."""

    TYPES = [
        ('VALIDATION', _('Validation')),
        ('RAPPEL', _('Rappel')),
        ('APPROBATION', _('Approbation')),
        ('REJET', _('Rejet')),
        ('INFO', _('Information')),
    ]

    destinataire = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('Destinataire')
    )

    titre = models.CharField(
        _('Titre'),
        max_length=200,
        help_text=_('Titre de la notification')
    )

    message = models.TextField(
        _('Message'),
        help_text=_('Contenu de la notification')
    )

    type = models.CharField(
        _('Type'),
        max_length=20,
        choices=TYPES,
        default='INFO',
        help_text=_('Type de notification')
    )

    lue = models.BooleanField(
        _('Lue'),
        default=False,
        help_text=_('La notification a-t-elle été lue ?')
    )

    date_creation = models.DateTimeField(
        _('Date de création'),
        auto_now_add=True
    )

    date_lecture = models.DateTimeField(
        _('Date de lecture'),
        null=True,
        blank=True
    )

    lien = models.URLField(
        _('Lien'),
        blank=True,
        help_text=_('Lien vers la ressource concernée')
    )

    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.titre} - {self.destinataire.get_full_name()}"


class AuditLog(models.Model):
    """Modèle pour les logs d'audit."""

    ACTIONS = [
        ('CREATE', _('Création')),
        ('UPDATE', _('Modification')),
        ('DELETE', _('Suppression')),
        ('VALIDATE', _('Validation')),
        ('REJECT', _('Rejet')),
        ('APPROVE', _('Approbation')),
    ]

    utilisateur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='audit_logs',
        verbose_name=_('Utilisateur')
    )

    action = models.CharField(
        _('Action'),
        max_length=20,
        choices=ACTIONS,
        help_text=_('Type d\'action effectuée')
    )

    model = models.CharField(
        _('Modèle'),
        max_length=100,
        help_text=_('Nom du modèle concerné')
    )

    object_id = models.UUIDField(
        _('ID de l\'objet'),
        help_text=_('UUID de l\'objet concerné')
    )

    old_value = models.TextField(
        _('Valeur ancienne'),
        null=True,
        blank=True,
        help_text=_('Valeur avant modification (JSON)')
    )

    new_value = models.TextField(
        _('Nouvelle valeur'),
        null=True,
        blank=True,
        help_text=_('Valeur après modification (JSON)')
    )

    ip_address = models.GenericIPAddressField(
        _('Adresse IP'),
        null=True,
        blank=True,
        help_text=_('Adresse IP de l\'utilisateur')
    )

    date_action = models.DateTimeField(
        _('Date de l\'action'),
        auto_now_add=True
    )

    class Meta:
        verbose_name = _('Log d\'audit')
        verbose_name_plural = _('Logs d\'audit')
        ordering = ['-date_action']

    def __str__(self):
        return f"{self.utilisateur.get_full_name()} - {self.action} - {self.model}"
