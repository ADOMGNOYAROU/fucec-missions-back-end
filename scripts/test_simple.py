#!/usr/bin/env python
"""
Test simple de l'intégration frontend/backend
"""
import requests
import json

def test_simple():
    print("🧪 TEST SIMPLE D'INTÉGRATION\n")

    # Test 1: Authentification
    print("1️⃣ TEST AUTHENTIFICATION")
    auth_url = "http://localhost:8000/api/users/auth/login/"
    auth_data = {"identifiant": "agent", "password": "test123"}

    try:
        response = requests.post(auth_url, json=auth_data, timeout=10)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✅ Authentification réussie")
            token = data.get('access')
            headers = {'Authorization': f'Bearer {token}'}

            # Test 2: Création simple
            print("\n2️⃣ TEST CRÉATION MISSION")
            mission_url = "http://localhost:8000/api/missions/"
            mission_data = {
                "titre": "Test Simple",
                "description": "Test simple de création",
                "type": "FORMATION",
                "date_debut": "2025-12-01",
                "date_fin": "2025-12-02",
                "lieu_mission": "Test",
                "budget_estime": 100000,
                "avance_demandee": 50000
            }

            create_response = requests.post(mission_url, json=mission_data, headers=headers, timeout=15)
            print(f"Status création: {create_response.status_code}")

            if create_response.status_code == 201:
                print("✅ Mission créée avec succès !")
                try:
                    mission = create_response.json()
                    print(f"   ID: {mission.get('id')}")
                    print(f"   Référence: {mission.get('reference')}")
                    print(f"   Statut: {mission.get('statut')}")
                    return True
                except:
                    print("   ❌ Erreur dans la réponse JSON")
                    return False
            else:
                print("❌ Échec création:")
                try:
                    error = create_response.json()
                    print(f"   Erreurs: {error}")
                except:
                    print(f"   Réponse brute: {create_response.text[:200]}")
                return False

        else:
            print("❌ Échec authentification")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ SERVEUR NON ACCESSIBLE")
        print("   Vérifiez que le serveur Django est démarré:")
        print("   cd backend && python manage.py runserver")
        return False
    except Exception as e:
        print(f"❌ ERREUR: {str(e)}")
        return False

if __name__ == '__main__':
    success = test_simple()
    if success:
        print("\n🎉 TEST RÉUSSI ! L'intégration fonctionne !")
    else:
        print("\n❌ TEST ÉCHOUÉ")
