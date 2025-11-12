#!/usr/bin/env python
"""
Script simple pour créer une mission de démonstration
"""
import os
import sys
import django
from datetime import date, timedelta

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fucec_missions.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from users.models import User, UserRole
from missions.models import Mission, MissionType, MissionStatus

def create_demo_mission():
    print('🚀 CRÉATION D\'UNE MISSION DE DÉMONSTRATION\n')

    # Récupérer un agent
    agent = User.objects.filter(role=UserRole.AGENT).first()
    if not agent:
        print('❌ Aucun agent trouvé. Veuillez créer des utilisateurs d\'abord.')
        return False

    print(f'Agent utilisé: {agent.get_full_name()} ({agent.identifiant})')

    # Créer la mission directement dans la base
    mission = Mission.objects.create(
        titre='Formation Développement Web - React/Angular',
        description='Participation à la formation sur les frameworks JavaScript modernes organisée par l\'INPHB.',
        type=MissionType.FORMATION,
        statut=MissionStatus.BROUILLON,
        date_debut=date.today() + timedelta(days=15),
        date_fin=date.today() + timedelta(days=18),
        lieu_mission='Yamoussoukro, Côte d\'Ivoire',
        budget_estime=750000.00,  # 750,000 FCFA
        avance_demandee=250000.00,  # 250,000 FCFA d'avance
        createur=agent
    )

    print('✅ Mission créée avec succès !')
    print(f'   ID: {mission.id}')
    print(f'   Référence: {mission.reference}')
    print(f'   Titre: {mission.titre}')
    print(f'   Statut: {mission.get_statut_display()}')
    print(f'   Dates: {mission.date_debut} au {mission.date_fin}')
    print(f'   Lieu: {mission.lieu_mission}')
    print(f'   Budget estimé: {mission.budget_estime:,.0f} FCFA')
    print(f'   Avance demandée: {mission.avance_demandee:,.0f} FCFA')
    print(f'   Créateur: {mission.createur.get_full_name()}')

    return True

if __name__ == '__main__':
    success = create_demo_mission()
    if success:
        print('\n🎯 Mission prête pour les tests !')
        print('Vous pouvez maintenant tester les endpoints API.')
    else:
        print('\n❌ Échec de la création de la mission.')
