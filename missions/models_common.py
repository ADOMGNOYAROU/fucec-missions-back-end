from django.db import models
from django.utils.translation import gettext_lazy as _

class TypeMission(models.Model):
    """Modèle pour les types de mission."""
    
    code = models.CharField(
        _('Code'),
        max_length=20,
        unique=True,
        help_text=_('Code unique du type de mission')
    )
    
    libelle = models.CharField(
        _('Libellé'),
        max_length=100,
        help_text=_('Libellé du type de mission')
    )
    
    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Description détaillée du type de mission')
    )
    
    actif = models.BooleanField(
        _('Actif'),
        default=True,
        help_text=_('Indique si ce type de mission est actif')
    )
    
    class Meta:
        verbose_name = _('Type de mission')
        verbose_name_plural = _('Types de mission')
        ordering = ['libelle']
    
    def __str__(self):
        return self.libelle


class TypeFrais(models.Model):
    """Modèle pour les types de frais."""
    
    code = models.CharField(
        _('Code'),
        max_length=20,
        unique=True,
        help_text=_('Code unique du type de frais')
    )
    
    libelle = models.CharField(
        _('Libellé'),
        max_length=100,
        help_text=_('Libellé du type de frais')
    )
    
    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Description détaillée du type de frais')
    )
    
    plafond = models.DecimalField(
        _('Plafond'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Plafond journalier en FCFA (si applicable)')
    )
    
    remboursable = models.BooleanField(
        _('Remboursable'),
        default=True,
        help_text=_('Indique si ce type de frais est remboursable')
    )
    
    actif = models.BooleanField(
        _('Actif'),
        default=True,
        help_text=_('Indique si ce type de frais est actif')
    )
    
    class Meta:
        verbose_name = _('Type de frais')
        verbose_name_plural = _('Types de frais')
        ordering = ['libelle']
    
    def __str__(self):
        return self.libelle
