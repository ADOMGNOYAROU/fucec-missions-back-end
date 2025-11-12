#!/usr/bin/env python
"""
Debug complet du système d'authentification
"""
import requests
import json

def test_full_auth_flow():
    print("🔍 DEBUG COMPLET AUTHENTIFICATION FRONTEND/BACKEND")
    print("=" * 60)

    # 1. Test des utilisateurs disponibles
    print("\n1️⃣ UTILISATEURS DISPONIBLES EN BASE")
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT identifiant, role, first_name, last_name FROM users_customuser")
            users = cursor.fetchall()
            print("Utilisateurs trouvés:")
            for user in users:
                identifiant, role, first_name, last_name = user
                print(f"   - {identifiant}: {role} ({first_name} {last_name})")
    except Exception as e:
        print(f"Erreur accès base: {e}")

    # 2. Test connexion avec différents utilisateurs
    test_users = [
        {"identifiant": "agent", "password": "test123", "expected_role": "AGENT"},
        {"identifiant": "chef_agence", "password": "test123", "expected_role": "CHEF_AGENCE"},
        {"identifiant": "admin", "password": "admin123", "expected_role": "ADMIN"}
    ]

    for i, user in enumerate(test_users, 3):
        print(f"\n{i}️⃣ TEST CONNEXION: {user['identifiant'].upper()}")

        try:
            auth_url = "http://localhost:8000/api/users/auth/login/"
            response = requests.post(auth_url, json={
                "identifiant": user["identifiant"],
                "password": user["password"]
            }, timeout=10)

            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                user_data = data.get('user', {})
                token = data.get('access', '')

                print(f"   ✅ Connexion réussie")
                print(f"   👤 {user_data.get('first_name')} {user_data.get('last_name')}")
                print(f"   🎭 Rôle: {user_data.get('role')}")
                print(f"   🔑 Token: {len(token)} caractères")

                # Test accès protégé
                headers = {'Authorization': f'Bearer {token}'}
                missions_response = requests.get("http://localhost:8000/api/missions/", headers=headers, timeout=10)

                if missions_response.status_code == 200:
                    missions = missions_response.json()
                    count = missions.get('count', 0)
                    print(f"   📋 Accès missions: ✅ ({count} missions)")
                else:
                    print(f"   📋 Accès missions: ❌ {missions_response.status_code}")

                # Test création mission
                mission_data = {
                    "titre": f"Test {user['identifiant']}",
                    "description": f"Test automatique pour {user['identifiant']}",
                    "type": "FORMATION",
                    "date_debut": "2025-12-15",
                    "date_fin": "2025-12-16",
                    "lieu_mission": "Test",
                    "budget_estime": 100000,
                    "avance_demandee": 50000
                }

                create_response = requests.post("http://localhost:8000/api/missions/", json=mission_data, headers=headers, timeout=10)

                if create_response.status_code == 201:
                    created = create_response.json()
                    print(f"   ✅ Création mission: {created.get('reference', 'N/A')}")
                else:
                    print(f"   ❌ Création mission: {create_response.status_code}")
                    print(f"      Erreur: {create_response.text[:100]}")

            else:
                print(f"   ❌ Échec connexion: {response.text}")

        except requests.exceptions.ConnectionError:
            print("   ❌ SERVEUR NON ACCESSIBLE")
        except Exception as e:
            print(f"   ❌ ERREUR: {str(e)}")

    # 3. Analyse des tokens JWT
    print("\n5️⃣ ANALYSE JWT")
    try:
        auth_response = requests.post("http://localhost:8000/api/users/auth/login/", json={
            "identifiant": "agent",
            "password": "test123"
        }, timeout=10)

        if auth_response.status_code == 200:
            token = auth_response.json().get('access')
            if token:
                # Décoder le JWT (sans vérification signature pour debug)
                import base64
                header, payload, signature = token.split('.')
                payload += '=' * (4 - len(payload) % 4)
                decoded = base64.urlsafe_b64decode(payload)
                claims = json.loads(decoded)

                import time
                exp_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(claims.get('exp', 0)))
                iat_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(claims.get('iat', 0)))

                print(f"   Token émis: {iat_time}")
                print(f"   Token expire: {exp_time}")
                print(f"   User ID: {claims.get('user_id')}")
                print(f"   Token type: {claims.get('token_type')}")

    except Exception as e:
        print(f"   Erreur analyse token: {e}")

    print("\n" + "=" * 60)
    print("🎯 RECOMMANDATIONS POUR LE FRONTEND:")
    print("   1. Vérifier que devAutoLogin: true dans environment.ts")
    print("   2. Vérifier que l'utilisateur 'agent' existe (role: AGENT)")
    print("   3. Ouvrir la console du navigateur (F12) pour voir les logs")
    print("   4. Vérifier localStorage pour 'access_token' et 'current_user'")
    print("   5. Redémarrer le serveur Angular: npm start")

if __name__ == '__main__':
    # Configuration Django
    import os
    import sys
    import django

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fucec_missions.settings')
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    django.setup()

    test_full_auth_flow()
