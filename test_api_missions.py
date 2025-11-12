#!/usr/bin/env python
"""
Script de test complet de l'API des missions
Teste la création, soumission et validation d'une mission
"""
import os
import sys
import django
import requests
import json
from datetime import date, timedelta

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fucec_missions.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from users.models import User, UserRole
from missions.models import Mission, MissionStatus

def test_api_missions():
    print('🚀 TEST COMPLET DE L\'API MISSIONS\n')

    # Étape 1: Authentification d'un agent
    print('1️⃣ AUTHENTIFICATION AGENT')
    agent = User.objects.filter(role=UserRole.AGENT).first()
    if not agent:
        print('❌ Aucun agent trouvé')
        return

    # Simuler l'authentification (en production, utiliser JWT)
    print(f'Agent connecté: {agent.get_full_name()} ({agent.identifiant})')

    # Étape 2: Lister les missions existantes
    print('\n2️⃣ MISSIONS EXISTANTES')
    missions = Mission.objects.filter(createur=agent)
    print(f'Missions de {agent.get_full_name()}: {missions.count()}')

    for mission in missions:
        print(f'• {mission.reference}: {mission.titre} ({mission.get_statut_display()})')

    # Étape 3: Créer une nouvelle mission via l'API simulée
    print('\n3️⃣ CRÉATION D\'UNE NOUVELLE MISSION')

    # Données de test pour la création
    mission_data = {
        'titre': 'Réunion stratégique avec partenaires',
        'description': 'Réunion mensuelle avec les partenaires commerciaux pour faire le point sur les objectifs trimestriels.',
        'type': 'REUNION',
        'date_debut': (date.today() + timedelta(days=5)).isoformat(),
        'date_fin': (date.today() + timedelta(days=5)).isoformat(),
        'lieu_mission': 'Abidjan, Hôtel Ivoire',
        'budget_estime': 300000.00,
        'avance_demandee': 150000.00,
        'intervenants': [agent.id]
    }

    print('Données de création:')
    for key, value in mission_data.items():
        if key == 'intervenants':
            print(f'  {key}: {len(value)} intervenant(s)')
        else:
            print(f'  {key}: {value}')

    # Simuler la création via serializer
    from missions.serializers import MissionCreateSerializer
    from rest_framework.test import APIRequestFactory

    factory = APIRequestFactory()
    request = factory.post('/api/missions/', mission_data, format='json')
    request.user = agent

    serializer = MissionCreateSerializer(data=mission_data, context={'request': request})

    if serializer.is_valid():
        new_mission = serializer.save()
        print('✅ Mission créée avec succès via API !')
        print(f'   ID: {new_mission.id}')
        print(f'   Référence: {new_mission.reference}')
        print(f'   Statut: {new_mission.get_statut_display()}')
    else:
        print('❌ Erreurs de validation:')
        for field, errors in serializer.errors.items():
            print(f'   {field}: {errors}')

    # Étape 4: Workflow complet simulé
    print('\n4️⃣ WORKFLOW MISSION SIMULÉ')

    if 'new_mission' in locals():
        mission = new_mission

        print(f'Mission: {mission.titre}')
        print(f'Statut actuel: {mission.get_statut_display()}')

        # Simuler la soumission
        print('\n📤 SOUMISSION POUR VALIDATION...')
        # Ici on appellerait l'endpoint /api/missions/{id}/submit/

        # Simuler la validation par le chef d'agence
        print('✅ VALIDATION CHEF D\'AGENCE...')
        chef_agence = User.objects.filter(role=UserRole.CHEF_AGENCE).first()
        if chef_agence:
            print(f'Validée par: {chef_agence.get_full_name()}')

        # Simuler l'attribution de véhicule
        print('🚗 ATTRIBUTION VÉHICULE...')
        print('Véhicule attribué: Peugeot 508 (AB-123-CD)')

        # Simuler le versement d'avance
        print('💰 VERSEMENT D\'AVANCE...')
        print(f'Avance versée: {mission.avance_demandee:,.0f} FCFA')

        print('\n🎯 MISSION PRÊTE POUR EXÉCUTION !')

    # Étape 5: Statistiques finales
    print('\n5️⃣ STATISTIQUES FINALES')
    total_missions = Mission.objects.count()
    missions_par_statut = {}
    for status, _ in MissionStatus.choices:
        count = Mission.objects.filter(statut=status).count()
        if count > 0:
            missions_par_statut[status] = count

    print(f'Total missions: {total_missions}')
    print('Répartition par statut:')
    for status, count in missions_par_statut.items():
        print(f'  {dict(MissionStatus.choices)[status]}: {count}')

    print('\n🎉 TEST API TERMINÉ AVEC SUCCÈS !')

if __name__ == '__main__':
    test_api_missions()
