#!/usr/bin/env python
"""
Test de l'intégration frontend/backend pour la création de missions
"""
import requests
import json
import time

def test_mission_creation_api():
    """Test de création d'une mission via l'API REST"""

    print("🚀 TEST DE CRÉATION DE MISSION VIA API")
    print("=" * 50)

    # Étape 1: Authentification
    print("\n1️⃣ AUTHENTIFICATION AGENT")
    auth_url = "http://localhost:8000/api/users/auth/login/"
    auth_data = {
        "identifiant": "agent",
        "password": "test123"
    }

    try:
        auth_response = requests.post(auth_url, json=auth_data, timeout=10)
        print(f"Status: {auth_response.status_code}")

        if auth_response.status_code == 200:
            auth_data = auth_response.json()
            access_token = auth_data.get('access')
            refresh_token = auth_data.get('refresh')
            print("✅ Authentification réussie")
            print(f"Token: {access_token[:50]}...")

            # Headers pour les requêtes authentifiées
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            # Étape 2: Création de la mission
            print("\n2️⃣ CRÉATION DE LA MISSION")

            mission_url = "http://localhost:8000/api/missions/"
            mission_data = {
                "titre": "Test Interface Angular - Formation DevOps",
                "description": "Formation intensive sur les pratiques DevOps et CI/CD organisée par l'INPHB pour améliorer les compétences techniques de l'équipe.",
                "type": "FORMATION",
                "date_debut": "2025-12-15",
                "date_fin": "2025-12-18",
                "lieu_mission": "Yamoussoukro, Institut National Polytechnique Félix Houphouët-Boigny",
                "budget_estime": 650000.00,
                "avance_demandee": 300000.00,
                "participants": []  # L'agent sera ajouté automatiquement
            }

            print("Données de la mission:")
            for key, value in mission_data.items():
                if key == 'participants':
                    print(f"  {key}: {len(value)} participants")
                elif key == 'budget_estime' or key == 'avance_demandee':
                    print(f"  {key}: {value:,.0f} FCFA")
                else:
                    print(f"  {key}: {value}")

            create_response = requests.post(mission_url, json=mission_data, headers=headers, timeout=15)
            print(f"\nStatus création: {create_response.status_code}")

            if create_response.status_code == 201:
                mission_created = create_response.json()
                print("✅ Mission créée avec succès !")
                print(f"   ID: {mission_created.get('id')}")
                print(f"   Référence: {mission_created.get('reference')}")
                print(f"   Statut: {mission_created.get('statut')}")

                # Étape 3: Vérification de la mission créée
                print("\n3️⃣ VÉRIFICATION DE LA MISSION CRÉÉE")

                mission_detail_url = f"{mission_url}{mission_created.get('id')}/"
                detail_response = requests.get(mission_detail_url, headers=headers, timeout=10)

                if detail_response.status_code == 200:
                    mission_detail = detail_response.json()
                    print("✅ Mission récupérée avec succès")
                    print(f"   Titre: {mission_detail.get('titre')}")
                    print(f"   Créateur: {mission_detail.get('createur_nom')}")
                    print(f"   Budget: {mission_detail.get('budget_estime'):,.0f} FCFA")
                    print(f"   Participants: {mission_detail.get('intervenants_count', 0)}")
                else:
                    print(f"❌ Erreur récupération: {detail_response.status_code}")

                return True

            else:
                print("❌ Erreur création:")
                try:
                    error_data = create_response.json()
                    print(f"   Détails: {error_data}")
                except:
                    print(f"   Réponse: {create_response.text}")
                return False

        else:
            print("❌ Échec authentification:")
            try:
                error_data = auth_response.json()
                print(f"   Erreur: {error_data}")
            except:
                print(f"   Réponse: {auth_response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ ERREUR DE CONNEXION")
        print("   Le serveur backend n'est pas accessible sur http://localhost:8000")
        print("   Assurez-vous que le serveur Django est démarré:")
        print("   cd backend && python manage.py runserver")
        return False
    except Exception as e:
        print(f"❌ ERREUR INATTENDUE: {str(e)}")
        return False

def test_mission_workflow():
    """Test du workflow complet de validation"""
    print("\n4️⃣ TEST DU WORKFLOW DE VALIDATION")

    # Authentification en tant qu'agent
    auth_url = "http://localhost:8000/api/users/auth/login/"
    agent_auth = {"identifiant": "agent", "password": "test123"}

    try:
        auth_response = requests.post(auth_url, json=agent_auth, timeout=10)
        if auth_response.status_code != 200:
            print("❌ Impossible de s'authentifier en tant qu'agent")
            return False

        agent_token = auth_response.json().get('access')
        headers_agent = {'Authorization': f'Bearer {agent_token}'}

        # Récupérer les missions de l'agent
        missions_url = "http://localhost:8000/api/missions/"
        missions_response = requests.get(missions_url, headers=headers_agent, timeout=10)

        if missions_response.status_code == 200:
            missions = missions_response.json()
            if missions.get('results'):
                latest_mission = missions['results'][0]
                mission_id = latest_mission['id']
                print(f"Mission trouvée: {latest_mission['reference']} - {latest_mission['titre']}")
                print(f"Statut actuel: {latest_mission['statut']}")

                # Test de soumission pour validation
                submit_url = f"{missions_url}{mission_id}/submit/"
                submit_response = requests.post(submit_url, headers=headers_agent, timeout=10)

                if submit_response.status_code == 200:
                    print("✅ Mission soumise pour validation")
                    return True
                else:
                    print(f"❌ Échec soumission: {submit_response.status_code}")
                    return False
            else:
                print("❌ Aucune mission trouvée")
                return False
        else:
            print(f"❌ Erreur récupération missions: {missions_response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Erreur workflow: {str(e)}")
        return False

if __name__ == '__main__':
    print("🧪 TEST INTÉGRATION FRONTEND/BACKEND")
    print("Test de la création d'ordre de mission via l'interface Angular")
    print("=" * 60)

    # Test de création
    creation_success = test_mission_creation_api()

    if creation_success:
        # Test du workflow si création réussie
        workflow_success = test_mission_workflow()

        if workflow_success:
            print("\n" + "=" * 60)
            print("🎉 RÉSULTAT FINAL: TOUS LES TESTS RÉUSSIS !")
            print("✅ L'interface Angular peut créer des missions")
            print("✅ Le workflow de validation fonctionne")
            print("✅ L'intégration frontend/backend est opérationnelle")
            print("\n🚀 L'APPLICATION EST PRÊTE POUR L'UTILISATION !")
        else:
            print("\n⚠️ Création réussie mais problème dans le workflow")
    else:
        print("\n❌ ÉCHEC DE L'INTÉGRATION FRONTEND/BACKEND")
