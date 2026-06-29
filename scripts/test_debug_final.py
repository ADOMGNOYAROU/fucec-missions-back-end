#!/usr/bin/env python
"""
Test rapide de l'auto-connexion améliorée
"""
import time
import requests

def test_auto_login_debug():
    print("🔧 TEST AUTO-CONNEXION AVEC DEBUG AMÉLIORÉ")
    print("=" * 50)

    # 1. Test backend accessible
    print("\n1️⃣ BACKEND ACCESSIBLE")
    try:
        response = requests.get("http://localhost:8000/api/users/auth/login/", timeout=5)
        print(f"   ✅ Backend: {response.status_code}")
    except:
        print("   ❌ Backend non accessible")
        return

    # 2. Test connexion API directe
    print("\n2️⃣ CONNEXION API DIRECTE")
    try:
        login_data = {
            "identifiant": "agent",
            "password": "test123"
        }
        response = requests.post(
            "http://localhost:8000/api/users/auth/login/",
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("   ✅ Login API: SUCCÈS")
            print(f"   👤 User: {data.get('user', {}).get('first_name')} {data.get('user', {}).get('last_name')}")
            print(f"   🎭 Role: {data.get('user', {}).get('role')}")
            print(f"   🔑 Access: {'OUI' if data.get('access') else 'NON'}")
            print(f"   🔄 Refresh: {'OUI' if data.get('refresh') else 'NON'}")

            # Test avec token
            access_token = data.get('access')
            if access_token:
                print("\n3️⃣ TEST AVEC TOKEN")
                headers = {"Authorization": f"Bearer {access_token}"}
                missions_response = requests.get("http://localhost:8000/api/missions/", headers=headers, timeout=10)
                print(f"   Status avec token: {missions_response.status_code}")

                if missions_response.status_code == 200:
                    print("   ✅ API avec token: FONCTIONNE")
                else:
                    print(f"   ❌ API avec token: ÉCHEC {missions_response.status_code}")
                    print(f"   Erreur: {missions_response.text[:100]}")
        else:
            print(f"   ❌ Login API: ÉCHEC {response.status_code}")
            print(f"   Erreur: {response.text}")

    except Exception as e:
        print(f"   ❌ ERREUR: {str(e)}")

    print("\n" + "=" * 50)
    print("🎯 INSTRUCTIONS POUR ANGULAR:")
    print("1. Ouvrir http://localhost:4200")
    print("2. Ouvrir Console (F12)")
    print("3. Rafraîchir la page")
    print("4. Chercher ces logs:")
    print("")
    print("✅ SUCCÈS ATTENDU:")
    print("   🚀 AuthService: Constructor appelé")
    print("   🔐 AuthService: Démarrage auto-connexion API forcée")
    print("   ✅ AuthService: Auto-connexion API réussie")
    print("   🔵 AuthInterceptor: Requête interceptée (pour chaque requête)")
    print("   🔑 AuthInterceptor: Token récupéré: OUI")
    print("")
    print("❌ SI ÉCHEC:")
    print("   ❌ AuthService: ÉCHEC AUTO-CONNEXION API")
    print("   + Détails de l'erreur affichés")
    print("")
    print("🔍 DEBUG ADDITIONNEL:")
    print("   Dans Console > Application > Local Storage")
    print("   Vérifier présence de:")
    print("   - access_token")
    print("   - refresh_token")
    print("   - current_user")

if __name__ == '__main__':
    test_auto_login_debug()
