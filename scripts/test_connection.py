"""
Script de test pour vérifier la connexion frontend-backend
"""
import requests
import json

# URL de base de l'API
API_URL = "http://127.0.0.1:8000/api"

def test_server_running():
    """Teste si le serveur Django est en cours d'exécution"""
    try:
        response = requests.get(f"{API_URL}/")
        print(f"✅ Serveur accessible - Status: {response.status_code}")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de contacter le serveur")
        print("   Assurez-vous que le serveur Django est démarré:")
        print("   python manage.py runserver")
        return False

def test_login_endpoint(identifiant, password):
    """Teste l'endpoint de connexion"""
    login_url = f"{API_URL}/users/auth/login/"
    
    print(f"\n🔐 Test de connexion avec l'identifiant: {identifiant}")
    
    try:
        response = requests.post(
            login_url,
            json={
                "identifiant": identifiant,
                "password": password
            },
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Connexion réussie!")
            print(f"   📝 Utilisateur: {data.get('user', {}).get('prenom')} {data.get('user', {}).get('nom')}")
            print(f"   👤 Rôle: {data.get('user', {}).get('role')}")
            print(f"   🔑 Token d'accès reçu: {data.get('access')[:20]}...")
            return True
        else:
            print(f"   ❌ Échec de la connexion")
            print(f"   Erreur: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur lors de la requête: {str(e)}")
        return False

def test_cors_headers():
    """Teste si les en-têtes CORS sont correctement configurés"""
    print("\n🌐 Test de la configuration CORS")
    
    try:
        response = requests.options(
            f"{API_URL}/users/auth/login/",
            headers={
                "Origin": "http://localhost:4200",
                "Access-Control-Request-Method": "POST"
            }
        )
        
        cors_headers = {
            "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
            "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
            "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers")
        }
        
        if cors_headers["Access-Control-Allow-Origin"]:
            print(f"   ✅ CORS configuré correctement")
            print(f"   Origin autorisée: {cors_headers['Access-Control-Allow-Origin']}")
            return True
        else:
            print(f"   ⚠️  CORS peut ne pas être correctement configuré")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur lors du test CORS: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("🧪 Test de connexion Frontend-Backend FUCEC Missions")
    print("=" * 60)
    
    # Test 1: Serveur en cours d'exécution
    if not test_server_running():
        return
    
    # Test 2: Configuration CORS
    test_cors_headers()
    
    # Test 3: Connexion avec différents utilisateurs
    print("\n" + "=" * 60)
    print("Test de connexion avec des utilisateurs de test")
    print("=" * 60)
    
    # Liste des utilisateurs de test courants
    test_users = [
        ("admin", "admin123"),
        ("admin.fucec", "test123"),
        ("dg.test", "password123"),
        ("chef.service.test", "password123"),
        ("agent.test", "password123"),
    ]
    
    success_count = 0
    for identifiant, password in test_users:
        if test_login_endpoint(identifiant, password):
            success_count += 1
    
    # Résumé
    print("\n" + "=" * 60)
    print(f"📊 Résultat: {success_count}/{len(test_users)} utilisateurs testés avec succès")
    print("=" * 60)
    
    if success_count > 0:
        print("\n✅ Le backend est prêt pour la connexion frontend!")
        print("\n📝 Pour démarrer le frontend:")
        print("   cd fucec-missions-frontend")
        print("   npm install")
        print("   ng serve")
        print("\n🌐 Ensuite ouvrez: http://localhost:4200")
    else:
        print("\n⚠️  Aucune connexion réussie. Vérifiez:")
        print("   1. Que les utilisateurs existent dans la base de données")
        print("   2. Que les mots de passe sont corrects")
        print("   3. Créez des utilisateurs via Django Admin:")
        print("      http://127.0.0.1:8000/admin/")

if __name__ == "__main__":
    main()
