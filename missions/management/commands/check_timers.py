"""
Commande Django pour vérifier les timers et envoyer les relances automatiques
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from missions.services import TimerService


class Command(BaseCommand):
    help = 'Vérifie les timers et envoie les relances automatiques pour les signatures et justificatifs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les actions sans les exécuter',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(
                self.style.WARNING('MODE DRY-RUN: Aucune action ne sera exécutée')
            )

        self.stdout.write(
            self.style.SUCCESS(f'Début de la vérification des timers à {timezone.now()}')
        )

        # 1. Vérifier les signatures en retard
        self.stdout.write('Vérification des signatures en retard...')
        try:
            if not dry_run:
                TimerService.check_overdue_signatures()
            self.stdout.write(
                self.style.SUCCESS('✓ Vérification des signatures terminée')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Erreur lors de la vérification des signatures: {e}')
            )

        # 2. Vérifier les justificatifs en retard
        self.stdout.write('Vérification des justificatifs en retard...')
        try:
            if not dry_run:
                TimerService.check_overdue_justificatifs()
            self.stdout.write(
                self.style.SUCCESS('✓ Vérification des justificatifs terminée')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Erreur lors de la vérification des justificatifs: {e}')
            )

        # 3. Vérifier les missions à archiver
        self.stdout.write('Vérification des missions à archiver...')
        try:
            if not dry_run:
                TimerService.check_missions_to_archive()
            self.stdout.write(
                self.style.SUCCESS('✓ Vérification d\'archivage terminée')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Erreur lors de la vérification d\'archivage: {e}')
            )

        self.stdout.write(
            self.style.SUCCESS(f'Fin de la vérification des timers à {timezone.now()}')
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING('MODE DRY-RUN: Relancer sans --dry-run pour exécuter les actions')
            )

