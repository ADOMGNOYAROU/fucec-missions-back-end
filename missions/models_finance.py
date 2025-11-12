from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import User


class Ticket(models.Model):
    """Modèle pour les tickets financiers."""

    STATUTS = [
        ('EMIS', _('Émis')),
        ('VALIDE', _('Validé')),
        ('ANNULE', _('Annulé')),
        ('PAYE', _('Payé')),
    ]

    numero = models.CharField(
        _('Numéro'),
        max_length=50,
        unique=True,
        help_text=_('Numéro unique du ticket')
    )

    mission = models.OneToOneField(
        'Mission',
        on_delete=models.CASCADE,
        related_name='ticket',
        verbose_name=_('Mission')
    )

    montant_approuve = models.DecimalField(
        _('Montant approuvé'),
        max_digits=12,
        decimal_places=2,
        help_text=_('Montant approuvé en FCFA')
    )

    date_emission = models.DateTimeField(
        _('Date d\'émission'),
        auto_now_add=True
    )

    emetteur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tickets_emis',
        verbose_name=_('Émetteur')
    )

    statut = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUTS,
        default='EMIS',
        help_text=_('Statut du ticket')
    )

    date_creation = models.DateTimeField(
        _('Date de création'),
        auto_now_add=True
    )

    class Meta:
        verbose_name = _('Ticket')
        verbose_name_plural = _('Tickets')
        ordering = ['-date_emission']

    def __str__(self):
        return f"Ticket {self.numero} - {self.mission.titre}"


class Avance(models.Model):
    """Modèle pour les avances financières."""

    STATUTS = [
        ('DEMANDEE', _('Demandée')),
        ('APPROUVEE', _('Approuvée')),
        ('VERSEEE', _('Versée')),
        ('ANNULEE', _('Annulée')),
        ('REMBOURSEE', _('Remboursée')),
    ]

    MODES_VERSEMENT = [
        ('ESPECES', _('Espèces')),
        ('VIREMENT', _('Virement bancaire')),
        ('CHEQUE', _('Chèque')),
    ]

    mission = models.ForeignKey(
        'Mission',
        on_delete=models.CASCADE,
        related_name='avances',
        verbose_name=_('Mission')
    )

    montant = models.DecimalField(
        _('Montant'),
        max_digits=12,
        decimal_places=2,
        help_text=_('Montant de l\'avance en FCFA')
    )

    date_versement = models.DateTimeField(
        _('Date de versement'),
        null=True,
        blank=True,
        help_text=_('Date à laquelle l\'avance a été versée')
    )

    verse_par = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='avances_versees',
        verbose_name=_('Versée par')
    )

    beneficiaire = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='avances_recues',
        verbose_name=_('Bénéficiaire')
    )

    statut = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUTS,
        default='DEMANDEE',
        help_text=_('Statut de l\'avance')
    )

    mode_versement = models.CharField(
        _('Mode de versement'),
        max_length=20,
        choices=MODES_VERSEMENT,
        default='ESPECES',
        help_text=_('Mode de versement de l\'avance')
    )

    date_creation = models.DateTimeField(
        _('Date de création'),
        auto_now_add=True
    )

    class Meta:
        verbose_name = _('Avance')
        verbose_name_plural = _('Avances')
        ordering = ['-date_creation']

    def __str__(self):
        return f"Avance {self.montant} FCFA - {self.mission.titre}"


class Depense(models.Model):
    """Modèle pour les dépenses de mission."""

    NATURES = [
        ('TRANSPORT', _('Transport')),
        ('HEBERGEMENT', _('Hébergement')),
        ('RESTAURATION', _('Restauration')),
        ('CARBURANT', _('Carburant')),
        ('PEAGE', _('Péage')),
        ('DIVERS', _('Dépenses diverses')),
    ]

    mission = models.ForeignKey(
        'Mission',
        on_delete=models.CASCADE,
        related_name='depenses',
        verbose_name=_('Mission')
    )

    nature = models.CharField(
        _('Nature'),
        max_length=20,
        choices=NATURES,
        help_text=_('Nature de la dépense')
    )

    montant = models.DecimalField(
        _('Montant'),
        max_digits=12,
        decimal_places=2,
        help_text=_('Montant de la dépense en FCFA')
    )

    date_depense = models.DateField(
        _('Date de dépense'),
        help_text=_('Date à laquelle la dépense a été effectuée')
    )

    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Description détaillée de la dépense')
    )

    date_creation = models.DateTimeField(
        _('Date de création'),
        auto_now_add=True
    )

    class Meta:
        verbose_name = _('Dépense')
        verbose_name_plural = _('Dépenses')
        ordering = ['-date_depense']

    def __str__(self):
        return f"{self.nature} - {self.montant} FCFA"
