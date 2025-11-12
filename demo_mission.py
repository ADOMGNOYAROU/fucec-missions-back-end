#!/usr/bin/env python
"""
Script de démonstration de création d'ordre de mission
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
from missions.serializers import MissionCreateSerializer

def demo_creation_mission():
    print('=== DÉMONSTRATION DE CRÉATION D\'ORDRE DE MISSION ===\n')

    # Récupérer un agent et un chef d'agence pour la démonstration
    try:
        agent = User.objects.filter(role=UserRole.AGENT).first()
        chef_agence = User.objects.filter(role=UserRole.CHEF_AGENCE).first()

        if not agent:
            print('❌ Aucun agent trouvé dans la base')
            return False

        print(f'Agent trouvé: {agent.get_full_name()} ({agent.identifiant})')
        print(f'Chef d\'agence trouvé: {chef_agence.get_full_name() if chef_agence else "Aucun"} ({chef_agence.identifiant if chef_agence else "N/A"})')
        print()

        # Créer une mission de démonstration
        print('📝 Création d\'une mission de démonstration...')

        # Données de la mission
        mission_data = {
            'titre': 'Mission de formation en Abidjan',
            'description': 'Formation sur les nouvelles technologies de gestion documentaire',
            'type': MissionType.FORMATION,
            'date_debut': date.today() + timedelta(days=7),
            'date_fin': date.today() + timedelta(days=10),
            'lieu_mission': 'Abidjan, Côte d\'Ivoire',
            'budget_prevu': 500000.00,  # 500,000 FCFA
            'objet_mission': 'Formation professionnelle',
            'entite_nom': 'Direction Informatique',
            'entite_type': 'Service',
            'intervenants': [agent.id]
        }

        # Simuler une requête avec l'utilisateur connecté
        from rest_framework.test import APIRequestFactory
        from django.contrib.auth.models import AnonymousUser

        factory = APIRequestFactory()
        request = factory.post('/api/missions/', mission_data, format='json')
        request.user = agent  # L'agent crée sa propre mission

        # Utiliser le serializer pour créer la mission
        serializer = MissionCreateSerializer(data=mission_data, context={'request': request})

        if serializer.is_valid():
            mission = serializer.save()
            print('✅ Mission créée avec succès !')
            print(f'   Référence: {mission.reference}')
            print(f'   Titre: {mission.titre}')
            print(f'   Statut: {mission.get_statut_display()}')
            print(f'   Créateur: {mission.createur.get_full_name()}')
            print(f'   Dates: {mission.date_debut} au {mission.date_fin}')
            print(f'   Lieu: {mission.lieu_mission}')
            print(f'   Budget: {mission.budget_prevu:,.0f} FCFA')
            print(f'   Intervenants: {mission.intervenants_count}')
            return True
        else:
            print('❌ Erreurs de validation:')
            for field, errors in serializer.errors.items():
                print(f'   {field}: {errors}')
            return False

    except Exception as e:
        print(f'❌ Erreur lors de la création: {str(e)}')
        return False

def lister_missions():
    print('\n=== MISSIONS EXISTANTES ===')
    missions = Mission.objects.all().order_by('-date_creation')[:5]

    if not missions:
        print('Aucune mission trouvée')
        return

    for mission in missions:
        print(f'• {mission.reference}: {mission.titre}')
        print(f'  Statut: {mission.get_statut_display()}')
        print(f'  Créateur: {mission.createur.get_full_name()}')
        print(f'  Dates: {mission.date_debut} - {mission.date_fin}')
        print()

def workflow_complet():
    print('=== WORKFLOW COMPLET D\'UNE MISSION ===\n')

    print('1. 📝 CRÉATION')
    print('   L\'agent crée sa demande de mission')

    print('2. 📤 SOUMISSION')
    print('   L\'agent soumet la mission pour validation')

    print('3. ✅ VALIDATION HIÉRARCHIQUE')
    print('   • Chef d\'agence → Responsable COPEC → DG')

    print('4. 🚗 MISSION EN COURS')
    print('   • Attribution de véhicule')
    print('   • Octroi d\'avances')

    print('5. 📋 DÉCLARATION DE RETOUR')
    print('   • L\'agent déclare son retour')

    print('6. 🧾 SOUMISSION JUSTIFICATIFS')
    print('   • Tickets de transport')
    print('   • Factures d\'hébergement')
    print('   • Notes de frais')

    print('7. 💰 VALIDATION FINANCIÈRE')
    print('   • Vérification par le comptable')
    print('   • Signature financière')

    print('8. 🔒 CLÔTURE')
    print('   Mission terminée et archivée')

if __name__ == '__main__':
    print('🚀 FUCEC MISSIONS - DÉMONSTRATION DE CRÉATION D\'ORDRE DE MISSION\n')

    # Lister les missions existantes
    lister_missions()

    # Démonstration de création
    success = demo_creation_mission()

    if success:
        # Relister après création
        lister_missions()

    # Expliquer le workflow
    workflow_complet()

    print('\n🎯 PRÊT POUR LES TESTS API !')
    print('Utilisez les endpoints suivants :')
    print('• POST /api/missions/ - Créer une mission')
    print('• GET /api/missions/ - Lister les missions')
    print('• POST /api/missions/{id}/submit/ - Soumettre pour validation')
    print('• POST /api/missions/{id}/validate/{decision}/ - Valider/Rejeter')
