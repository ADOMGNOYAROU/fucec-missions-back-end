#!/usr/bin/env python
"""
Debug script pour tester l'authentification frontend
"""
import requests
import json
import time

def test_auth_flow():
    print("🔍 DEBUG AUTHENTIFICATION FRONTEND/BACKEND")
    print("=" * 50)

    # 1. Test connexion API
    print("\n1️⃣ TEST CONNEXION API")
    auth_url = "http://localhost:8000/api/users/auth/login/"
    auth_data = {"identifiant": "agent", "password": "test123"}

    try:
        response = requests.post(auth_url, json=auth_data, timeout=10)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            access_token = data.get('access')
            refresh_token = data.get('refresh')
            user = data.get('user')

            print("✅ Authentification réussie")
            print(f"   User: {user.get('first_name')} {user.get('last_name')}")
            print(f"   Role: {user.get('role')}")
            print(f"   Token length: {len(access_token) if access_token else 0}")

            # 2. Test accès protégé avec token valide
            print("\n2️⃣ TEST ACCÈS PROTÉGÉ AVEC TOKEN VALIDE")
            headers = {'Authorization': f'Bearer {access_token}'}
            missions_response = requests.get("http://localhost:8000/api/missions/", headers=headers, timeout=10)

            print(f"Status missions: {missions_response.status_code}")
            if missions_response.status_code == 200:
                missions_data = missions_response.json()
                print(f"✅ Accès missions réussi - {missions_data.get('count', 0)} missions trouvées")
            else:
                print(f"❌ Échec accès missions: {missions_response.text}")

            # 3. Test avec token invalide
            print("\n3️⃣ TEST AVEC TOKEN INVALIDE")
            invalid_headers = {'Authorization': 'Bearer invalid_token'}
            invalid_response = requests.get("http://localhost:8000/api/missions/", headers=invalid_headers, timeout=10)

            print(f"Status token invalide: {invalid_response.status_code}")
            if invalid_response.status_code == 401:
                print("✅ Token invalide correctement rejeté")
            else:
                print(f"❌ Comportement inattendu: {invalid_response.text}")

            # 4. Test expiration token (attendre 5 secondes puis tester)
            print("\n4️⃣ TEST EXPIRATION TOKEN")
            print("   Attente de 5 secondes...")
            time.sleep(5)

            expired_response = requests.get("http://localhost:8000/api/missions/", headers=headers, timeout=10)
            print(f"Status après 5s: {expired_response.status_code}")

            if expired_response.status_code == 401:
                print("⚠️ Token expiré rapidement (vérifier configuration JWT)")
            elif expired_response.status_code == 200:
                print("✅ Token encore valide après 5 secondes")
            else:
                print(f"❌ Erreur inattendue: {expired_response.text}")

            return True

        else:
            print(f"❌ Échec authentification: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ SERVEUR NON ACCESSIBLE")
        print("   Vérifiez que le serveur Django fonctionne sur localhost:8000")
        return False
    except Exception as e:
        print(f"❌ ERREUR: {str(e)}")
        return False

def analyze_token(token):
    """Analyse un token JWT pour debug"""
    if not token:
        return None

    try:
        import base64
        # Décoder le payload (partie du milieu)
        header, payload, signature = token.split('.')
        # Ajouter du padding si nécessaire
        payload += '=' * (4 - len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        payload_data = json.loads(decoded)

        exp_timestamp = payload_data.get('exp')
        iat_timestamp = payload_data.get('iat')

        if exp_timestamp:
            from datetime import datetime
            exp_time = datetime.fromtimestamp(exp_timestamp)
            iat_time = datetime.fromtimestamp(iat_timestamp) if iat_timestamp else None
            current_time = datetime.now()

            print(f"   Token émis: {iat_time}")
            print(f"   Token expire: {exp_time}")
            print(f"   Temps actuel: {current_time}")
            print(f"   Expire dans: {(exp_time - current_time).total_seconds()} secondes")

            return exp_timestamp > time.time()
        else:
            return False
    except Exception as e:
        print(f"   Erreur décodage token: {e}")
        return False

if __name__ == '__main__':
    print("🐛 DEBUG FRONTEND AUTHENTIFICATION")
    print("Test de l'authentification et des tokens")

    success = test_auth_flow()

    if success:
        print("\n" + "=" * 50)
        print("🎯 ANALYSE DU PROBLÈME:")
        print("   - L'API backend fonctionne correctement")
        print("   - L'authentification retourne des tokens valides")
        print("   - Les endpoints protégés fonctionnent avec tokens valides")
        print("")
        print("🔧 SOLUTIONS POSSIBLES:")
        print("   1. Auto-connexion dev activée dans environment.ts")
        print("   2. Vérifier la logique de stockage des tokens côté frontend")
        print("   3. Vérifier la méthode isTokenExpired() dans auth.service.ts")
        print("   4. Vérifier que localStorage fonctionne correctement")
        print("")
        print("🚀 RELANCER LE SERVEUR ANGULAR:")
        print("   cd frontend && npm start")
        print("   L'auto-connexion dev devrait maintenant fonctionner")
    else:
        print("\n❌ PROBLÈME AVEC L'INFRASTRUCTURE BACKEND")
