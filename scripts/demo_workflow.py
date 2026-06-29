#!/usr/bin/env python
"""
Script de démonstration complet de la gestion des missions FUCEC
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
from missions.models import Mission, MissionStatus, MissionType
from missions.serializers import MissionCreateSerializer
from rest_framework.test import APIRequestFactory

def demo_complet_missions():
    print('🚀 FUCEC MISSIONS - DÉMONSTRATION COMPLÈTE\n')

    # 1. Préparation des utilisateurs
    print('1️⃣ PRÉPARATION DES UTILISATEURS')
    agent = User.objects.filter(role=UserRole.AGENT).first()
    chef_agence = User.objects.filter(role=UserRole.CHEF_AGENCE).first()

    if not agent:
        print('❌ Aucun agent trouvé')
        return

    print(f'Agent: {agent.get_full_name()} ({agent.identifiant})')
    print(f'Chef d\'agence: {chef_agence.get_full_name() if chef_agence else "N/A"}')

    # 2. État initial des missions
    print('\n2️⃣ ÉTAT INITIAL DES MISSIONS')
    total_missions = Mission.objects.count()
    print(f'Total missions: {total_missions}')

    missions_agent = Mission.objects.filter(createur=agent)
    print(f'Missions de {agent.get_full_name()}: {missions_agent.count()}')

    # 3. Création d'une nouvelle mission
    print('\n3️⃣ CRÉATION D\'UNE NOUVELLE MISSION')

    factory = APIRequestFactory()

    mission_data = {
        'titre': 'Réunion stratégique avec partenaires',
        'description': 'Réunion mensuelle avec les partenaires commerciaux pour faire le point sur les objectifs trimestriels.',
        'type': 'REUNION',
        'date_debut': (date.today() + timedelta(days=5)).isoformat(),
        'date_fin': (date.today() + timedelta(days=5)).isoformat(),
        'lieu_mission': 'Abidjan, Hôtel Ivoire',
        'budget_estime': 300000.00,
        'avance_demandee': 150000.00,
        'participants': [agent.id]
    }

    # Simuler la requête POST
    request = factory.post('/api/missions/', mission_data, format='json')
    request.user = agent

    serializer = MissionCreateSerializer(data=mission_data, context={'request': request})

    if serializer.is_valid():
        nouvelle_mission = serializer.save()
        print('✅ Nouvelle mission créée avec succès !')
        print(f'   Référence: {nouvelle_mission.reference}')
        print(f'   Titre: {nouvelle_mission.titre}')
        print(f'   Type: {nouvelle_mission.get_type_display()}')
        print(f'   Statut: {nouvelle_mission.get_statut_display()}')
        print(f'   Dates: {nouvelle_mission.date_debut} au {nouvelle_mission.date_fin}')
        print(f'   Lieu: {nouvelle_mission.lieu_mission}')
        print(f'   Budget estimé: {nouvelle_mission.budget_estime:,.0f} FCFA')
        print(f'   Avance demandée: {nouvelle_mission.avance_demandee:,.0f} FCFA')
    else:
        print('❌ Erreur lors de la création:')
        for field, errors in serializer.errors.items():
            print(f'   {field}: {errors}')
        return

    # 4. Simulation du workflow complet
    print('\n4️⃣ SIMULATION DU WORKFLOW COMPLET')

    print('📝 STATUT INITIAL: BROUILLON')
    print(f'   Statut: {nouvelle_mission.get_statut_display()}')

    # Simuler la soumission
    print('\n📤 ÉTAPE 1: SOUMISSION POUR VALIDATION')
    # Dans une vraie API, on appellerait POST /api/missions/{id}/submit/
    nouvelle_mission.statut = MissionStatus.EN_ATTENTE
    nouvelle_mission.save()
    print(f'   ✅ Soumise - Nouveau statut: {nouvelle_mission.get_statut_display()}')

    # Simuler la validation
    print('\n✅ ÉTAPE 2: VALIDATION HIÉRARCHIQUE')
    if chef_agence:
        print(f'   👔 Validée par {chef_agence.get_full_name()} (Chef d\'agence)')
        nouvelle_mission.statut = MissionStatus.VALIDEE
        nouvelle_mission.save()
        print(f'   ✅ Validée - Nouveau statut: {nouvelle_mission.get_statut_display()}')

    # Simuler le départ en mission
    print('\n🚗 ÉTAPE 3: DÉPART EN MISSION')
    nouvelle_mission.statut = MissionStatus.EN_COURS
    nouvelle_mission.date_debut_reelle = django.utils.timezone.now()
    nouvelle_mission.save()
    print(f'   ✅ Mission démarrée - Statut: {nouvelle_mission.get_statut_display()}')

    # Simuler le retour
    print('\n🏠 ÉTAPE 4: DÉCLARATION DE RETOUR')
    nouvelle_mission.statut = MissionStatus.RETOUR
    nouvelle_mission.retour_declare = True
    nouvelle_mission.date_retour_reelle = django.utils.timezone.now()
    nouvelle_mission.save()
    print(f'   ✅ Retour déclaré - Statut: {nouvelle_mission.get_statut_display()}')

    # 5. Statistiques finales
    print('\n5️⃣ STATISTIQUES FINALES')
    total_apres = Mission.objects.count()
    print(f'Total missions après création: {total_apres}')

    # Répartition par statut
    print('\n📊 RÉPARTITION PAR STATUT:')
    for status, label in MissionStatus.choices:
        count = Mission.objects.filter(statut=status).count()
        if count > 0:
            print(f'   {label}: {count}')

    # 6. Guide API
    print('\n6️⃣ GUIDE DES ENDPOINTS API')
    print('📋 Création de mission:')
    print('   POST /api/missions/')
    print('   Body: {"titre": "...", "description": "...", "type": "...", ...}')

    print('\n📤 Soumission pour validation:')
    print('   POST /api/missions/{id}/submit/')

    print('\n✅ Validation/Rejet:')
    print('   POST /api/missions/{id}/validate/{decision}/')

    print('\n📋 Liste des missions:')
    print('   GET /api/missions/')

    print('\n📝 Détail d\'une mission:')
    print('   GET /api/missions/{id}/')

    print('\n🎯 WORKFLOW COMPLET TERMINÉ AVEC SUCCÈS !')

if __name__ == '__main__':
    demo_complet_missions()
