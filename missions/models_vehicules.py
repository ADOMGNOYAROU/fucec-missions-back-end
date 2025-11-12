from django.db import models
from django.utils.translation import gettext_lazy as _


class Vehicule(models.Model):
    """Modèle pour les véhicules de service."""

    VEHICULE_TYPES = [
        ('VOITURE', _('Voiture')),
        ('MOTO', _('Moto')),
        ('CAMION', _('Camion')),
        ('BUS', _('Bus')),
    ]

    immatriculation = models.CharField(
        _('Immatriculation'),
        max_length=20,
        unique=True,
        help_text=_('Numéro d\'immatriculation')
    )

    marque = models.CharField(
        _('Marque'),
        max_length=50,
        help_text=_('Marque du véhicule')
    )

    modele = models.CharField(
        _('Modèle'),
        max_length=50,
        help_text=_('Modèle du véhicule')
    )

    type = models.CharField(
        _('Type'),
        max_length=20,
        choices=VEHICULE_TYPES,
        default='VOITURE',
        help_text=_('Type de véhicule')
    )

    disponible = models.BooleanField(
        _('Disponible'),
        default=True,
        help_text=_('Le véhicule est-il disponible ?')
    )

    kilometrage = models.PositiveIntegerField(
        _('Kilométrage'),
        default=0,
        help_text=_('Kilométrage actuel')
    )

    date_acquisition = models.DateField(
        _('Date d\'acquisition'),
        help_text=_('Date d\'acquisition du véhicule')
    )

    date_assurance = models.DateField(
        _('Date d\'assurance'),
        help_text=_('Date d\'expiration de l\'assurance')
    )

    date_visite = models.DateField(
        _('Date de visite'),
        help_text=_('Date de la prochaine visite technique')
    )

    date_creation = models.DateTimeField(
        _('Date de création'),
        auto_now_add=True
    )

    class Meta:
        verbose_name = _('Véhicule')
        verbose_name_plural = _('Véhicules')
        ordering = ['immatriculation']

    def __str__(self):
        return f"{self.immatriculation} - {self.marque} {self.modele}"


class Bareme(models.Model):
    """Modèle pour les barèmes de mission."""

    destination = models.CharField(
        _('Destination'),
        max_length=100,
        help_text=_('Destination de la mission')
    )

    fonction = models.CharField(
        _('Fonction'),
        max_length=100,
        help_text=_('Fonction du personnel')
    )

    montant_par_jour = models.DecimalField(
        _('Montant par jour'),
        max_digits=10,
        decimal_places=2,
        help_text=_('Montant journalier en FCFA')
    )

    date_debut = models.DateField(
        _('Date de début'),
        help_text=_('Date de début de validité')
    )

    date_fin = models.DateField(
        _('Date de fin'),
        null=True,
        blank=True,
        help_text=_('Date de fin de validité')
    )

    actif = models.BooleanField(
        _('Actif'),
        default=True,
        help_text=_('Le barème est-il actif ?')
    )

    date_creation = models.DateTimeField(
        _('Date de création'),
        auto_now_add=True
    )

    class Meta:
        verbose_name = _('Barème')
        verbose_name_plural = _('Barèmes')
        ordering = ['-date_debut', 'destination']
        unique_together = ['destination', 'fonction', 'date_debut']

    def __str__(self):
        return f"{self.destination} - {self.fonction} : {self.montant_par_jour} FCFA/jour"
