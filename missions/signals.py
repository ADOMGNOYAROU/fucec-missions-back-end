from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Mission, Validation, ValidationStatus, ValidationNiveau
from .models_missions import OrdreMission, HistoriqueMission
from django.db import transaction

@receiver(post_save, sender=Mission)
def creer_ordre_mission_apres_validation_dg(sender, instance, created, **kwargs):
    """
    Crée automatiquement un ordre de mission après la validation du DG.
    """
    # Vérifier si la mission vient d'être validée par le DG
    if instance.statut == 'VALIDEE' and not hasattr(instance, 'ordre_mission'):
        # Vérifier que la validation du DG est complète
        validation_dg = instance.validations.filter(
            niveau=ValidationNiveau.DGA_DG,
            statut=ValidationStatus.VALIDEE
        ).exists()
        
        if validation_dg:
            with transaction.atomic():
                # Créer l'ordre de mission
                ordre = OrdreMission.objects.create(
                    mission=instance,
                    statut='VALIDE',
                    date_signature=timezone.now()
                )
                
                # Générer une référence pour l'ordre de mission
                annee = timezone.now().year
                dernier_ordre = OrdreMission.objects.filter(
                    reference__startswith=f"OM-{annee}-"
                ).order_by('reference').last()
                
                if dernier_ordre:
                    try:
                        numero = int(dernier_ordre.reference.split('-')[-1]) + 1
                    except (IndexError, ValueError):
                        numero = 1
                else:
                    numero = 1
                
                ordre.reference = f"OM-{annee}-{numero:04d}"
                ordre.save()
                
                # Mettre à jour la mission avec l'ordre de mission
                instance.ordre_mission = ordre
                instance.save(update_fields=['statut'])
                
                # Créer une entrée dans l'historique
                HistoriqueMission.objects.create(
                    mission=instance,
                    utilisateur=instance.validations.get(
                        niveau=ValidationNiveau.DGA_DG
                    ).valideur,
                    action=f"Ordre de mission {ordre.reference} généré automatiquement",
                    details={
                        'ordre_mission_id': ordre.id,
                        'reference': ordre.reference
                    }
                )
