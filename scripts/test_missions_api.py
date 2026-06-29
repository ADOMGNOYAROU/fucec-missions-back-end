"""
Script de test pour diagnostiquer l'erreur 500 sur l'API missions
"""
import requests
import json

# URL de base de l'API
API_URL = "http://127.0.0.1:8000/api"

def test_login():
    """Teste la connexion et récupère un token"""
    print("🔐 Test de connexion...")
    
    login_data = {
        "identifiant": "kabila",
        "password": "majoie1234"  # Utiliser le mot de passe correct
    }
    
    try:
        response = requests.post(
            f"{API_URL}/users/auth/login/",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Connexion réussie!")
            print(f"   📝 Utilisateur: {data.get('user', {}).get('prenom')} {data.get('user', {}).get('nom')}")
            print(f"   👤 Rôle: {data.get('user', {}).get('role')}")
            return data.get('access'), data.get('user')
        else:
            print(f"   ❌ Échec de la connexion")
            print(f"   Erreur: {response.text}")
            return None, None
            
    except Exception as e:
        print(f"   ❌ Erreur lors de la requête: {str(e)}")
        return None, None

def test_missions_list(token):
    """Teste l'accès à la liste des missions"""
    print("\n📋 Test d'accès à la liste des missions...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"{API_URL}/missions/",
            headers=headers
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Accès réussi!")
            print(f"   📊 Nombre de missions: {len(data.get('results', [])) if isinstance(data, dict) and 'results' in data else len(data) if isinstance(data, list) else 'N/A'}")
            return True
        else:
            print(f"   ❌ Échec de l'accès")
            print(f"   Erreur: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur lors de la requête: {str(e)}")
        return False

def test_mission_model():
    """Teste si le modèle Mission est correctement configuré"""
    print("\n🏗️  Test du modèle Mission...")
    
    import os
    import sys
    import django
    from django.conf import settings
    
    # Ajouter le chemin du projet
    sys.path.append(os.path.join(os.path.dirname(__file__)))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fucec_missions.settings')
    
    try:
        django.setup()
        print("   ✅ Django initialisé")
        
        # Importer les modèles
        from missions.models import Mission
        
        # Créer une mission de test
        mission_count = Mission.objects.count()
        print(f"   📊 Nombre de missions existantes: {mission_count}")
        
        print("   ✅ Modèle Mission OK")
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur avec le modèle Mission: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("🧪 Diagnostic de l'API Missions - Erreur 500")
    print("=" * 60)
    
    # Test 1: Modèle Mission
    test_mission_model()
    
    # Test 2: Connexion
    token, user = test_login()
    
    if token and user:
        # Test 3: Accès aux missions
        test_missions_list(token)
    else:
        print("\n⚠️  Impossible de tester l'accès aux missions sans authentification")
    
    print("\n" + "=" * 60)
    print("Diagnostic terminé")
    print("=" * 60)

if __name__ == "__main__":
    main()
