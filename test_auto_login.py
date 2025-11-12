#!/usr/bin/env python
"""
Test rapide de l'auto-connexion API
"""
import requests
import time

def test_auto_login_api():
    print("🚀 TEST AUTO-CONNEXION API ANGULAR")
    print("=" * 40)

    # Test backend accessible
    print("1️⃣ Test backend accessible...")
    try:
        response = requests.get("http://localhost:8000/api/users/auth/login/", timeout=5)
        print(f"   ✅ Backend accessible: {response.status_code}")
    except:
        print("   ❌ Backend non accessible - démarrer: python manage.py runserver")
        return

    # Test connexion agent
    print("\n2️⃣ Test connexion agent...")
    try:
        auth_response = requests.post(
            "http://localhost:8000/api/users/auth/login/",
            json={"identifiant": "agent", "password": "test123"},
            timeout=10
        )

        if auth_response.status_code == 200:
            data = auth_response.json()
            user = data['user']
            token = data['access']

            print(f"   ✅ Connexion réussie: {user['first_name']} {user['last_name']}")
            print(f"   🎭 Rôle: {user['role']}")
            print(f"   🔑 Token valide: {len(token)} caractères")

            # Test accès protégé
            headers = {'Authorization': f'Bearer {token}'}
            missions_response = requests.get("http://localhost:8000/api/missions/", headers=headers, timeout=10)

            if missions_response.status_code == 200:
                missions = missions_response.json()
                print(f"   📋 API missions accessible: {missions['count']} missions")
            else:
                print(f"   ❌ API missions inaccessible: {missions_response.status_code}")

        else:
            print(f"   ❌ Échec connexion: {auth_response.status_code}")
            print(f"   Erreur: {auth_response.text[:100]}")

    except Exception as e:
        print(f"   ❌ Erreur connexion: {str(e)}")

    print("\n3️⃣ INSTRUCTIONS POUR ANGULAR:")
    print("   ✅ Configuration OK:")
    print("      - autoLoginEnabled: true")
    print("      - autoLoginCredentials: agent/test123")
    print("      - devAutoLogin: false")
    print("")
    print("   🚀 Démarrer Angular:")
    print("      cd frontend")
    print("      npm start")
    print("")
    print("   🔍 Vérifier console:")
    print("      - 'Auto-connexion API en cours avec agent simple...'")
    print("      - 'Auto-connexion API réussie'")
    print("")
    print("   ✅ Résultat attendu:")
    print("      - Navigation fluide vers /missions")
    print("      - Pas de redirection login")
    print("      - Formulaire création accessible")

if __name__ == '__main__':
    test_auto_login_api()
