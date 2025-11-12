#!/usr/bin/env python
"""
Test complet de l'authentification JWT
"""
import requests
import json

def test_jwt_flow():
    print("🔐 TEST COMPLET JWT ANGULAR + DJANGO")
    print("=" * 50)

    # 1. Test connexion
    print("\n1️⃣ TEST CONNEXION")
    try:
        login_response = requests.post(
            "http://localhost:8000/api/users/auth/login/",
            json={"identifiant": "agent", "password": "test123"},
            headers={"Content-Type": "application/json"}
        )

        print(f"Status: {login_response.status_code}")

        if login_response.status_code == 200:
            login_data = login_response.json()
            print("✅ Connexion réussie")
            print(f"Access token: {login_data.get('access', 'MANQUANT')[:30]}...")
            print(f"Refresh token: {login_data.get('refresh', 'MANQUANT')[:30]}...")
            print(f"User: {login_data.get('user', {}).get('first_name', 'N/A')}")

            access_token = login_data.get('access')
            refresh_token = login_data.get('refresh')

            if not access_token or not refresh_token:
                print("❌ ERREUR: Tokens manquants dans la réponse !")
                print(f"Clés disponibles: {list(login_data.keys())}")
                return

            # 2. Test requête avec token
            print("\n2️⃣ TEST REQUÊTE AUTHENTIFIÉE")
            headers = {"Authorization": f"Bearer {access_token}"}

            missions_response = requests.get(
                "http://localhost:8000/api/missions/",
                headers=headers
            )

            print(f"Status: {missions_response.status_code}")

            if missions_response.status_code == 200:
                print("✅ Requête authentifiée réussie")
                missions = missions_response.json()
                print(f"Missions trouvées: {missions.get('count', 0)}")
            else:
                print(f"❌ Requête échouée: {missions_response.status_code}")
                print(f"Erreur: {missions_response.text}")

                # 3. Test refresh token
                print("\n3️⃣ TEST REFRESH TOKEN")
                refresh_response = requests.post(
                    "http://localhost:8000/api/users/auth/token/refresh/",
                    json={"refresh": refresh_token},
                    headers={"Content-Type": "application/json"}
                )

                print(f"Refresh Status: {refresh_response.status_code}")

                if refresh_response.status_code == 200:
                    refresh_data = refresh_response.json()
                    new_access = refresh_data.get('access')
                    print("✅ Refresh réussi")
                    print(f"Nouveau access token: {new_access[:30]}...")

                    # Test avec nouveau token
                    print("\n4️⃣ TEST AVEC NOUVEAU TOKEN")
                    new_headers = {"Authorization": f"Bearer {new_access}"}
                    new_response = requests.get(
                        "http://localhost:8000/api/missions/",
                        headers=new_headers
                    )
                    print(f"Nouveau test Status: {new_response.status_code}")
                    if new_response.status_code == 200:
                        print("✅ Nouveau token fonctionne")
                    else:
                        print("❌ Nouveau token ne fonctionne pas")
                else:
                    print(f"❌ Refresh échoué: {refresh_response.status_code}")
                    print(f"Erreur refresh: {refresh_response.text}")

        else:
            print(f"❌ Connexion échouée: {login_response.status_code}")
            print(f"Erreur: {login_response.text}")

    except Exception as e:
        print(f"❌ ERREUR: {str(e)}")

    print("\n" + "=" * 50)
    print("📋 DIAGNOSTIC:")
    print("Si les tokens sont présents mais que les requêtes échouent:")
    print("1. Vérifier que l'intercepteur Angular est enregistré")
    print("2. Vérifier que le header Authorization est bien envoyé")
    print("3. Vérifier que Django reçoit bien le header")

if __name__ == '__main__':
    test_jwt_flow()
