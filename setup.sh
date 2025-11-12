#!/bin/bash

# Script de configuration du backend FUCEC Missions
# À exécuter depuis le dossier fucec-missions-backend

echo "🚀 Configuration du backend FUCEC Missions"
echo "=========================================="

# Activer l'environnement virtuel
echo "📦 Activation de l'environnement virtuel..."
source venv/Scripts/activate

# Installer les dépendances
echo "📦 Installation des dépendances..."
pip install -r requirements.txt

# Créer le fichier .env si nécessaire
if [ ! -f .env ]; then
    echo "📄 Création du fichier .env..."
    cp .env.example .env
    echo "⚠️  Veuillez éditer le fichier .env avec vos paramètres PostgreSQL"
fi

# Faire les migrations
echo "🗃️  Création des migrations..."
python manage.py makemigrations

echo "🗃️  Application des migrations..."
python manage.py migrate

# Créer un superutilisateur
echo "👤 Création d'un superutilisateur..."
echo "from users.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'admin123')" | python manage.py shell

# Créer des données de test
echo "📊 Création des données de test..."
python manage.py shell -c "
from users.models import User
from missions.models import Mission, MissionIntervenant

# Créer les utilisateurs de test
users_data = [
    {'identifiant': 'chef.agence.test', 'nom': 'Chef', 'prenom': 'Agence', 'email': 'chef.agence@example.com', 'role': 'CHEF_AGENCE'},
    {'identifiant': 'agent.test', 'nom': 'Agent', 'prenom': 'Simple', 'email': 'agent@example.com', 'role': 'AGENT'},
    {'identifiant': 'dg.test', 'nom': 'Direction', 'prenom': 'Générale', 'email': 'dg@example.com', 'role': 'DG'},
    {'identifiant': 'rh.test', 'nom': 'Ressources', 'prenom': 'Humaines', 'email': 'rh@example.com', 'role': 'RH'},
    {'identifiant': 'comptable.test', 'nom': 'Comptable', 'prenom': 'Principal', 'email': 'comptable@example.com', 'role': 'COMPTABLE'},
    {'identifiant': 'admin.test', 'nom': 'Administrateur', 'prenom': 'Système', 'email': 'admin@example.com', 'role': 'ADMIN'},
    {'identifiant': 'responsable.copec.test', 'nom': 'Directeur', 'prenom': 'Services', 'email': 'responsable.copec@example.com', 'role': 'RESPONSABLE_COPEC'},
    {'identifiant': 'agent2.test', 'nom': 'Agent', 'prenom': 'Deuxième', 'email': 'agent2@example.com', 'role': 'AGENT'},
    {'identifiant': 'chef.service.test', 'nom': 'Chef', 'prenom': 'Service', 'email': 'chef.service@example.com', 'role': 'CHEF_AGENCE'}
]

for user_data in users_data:
    user, created = User.objects.get_or_create(
        identifiant=user_data['identifiant'],
        defaults={
            'nom': user_data['nom'],
            'prenom': user_data['prenom'],
            'email': user_data['email'],
            'role': user_data['role']
        }
    )
    if created:
        user.set_password('password123')
        user.save()
        print(f'Utilisateur créé: {user.identifiant}')
    else:
        print(f'Utilisateur existe déjà: {user.identifiant}')

# Configurer les managers
chef_agence = User.objects.get(identifiant='chef.agence.test')
agent = User.objects.get(identifiant='agent.test')
agent2 = User.objects.get(identifiant='agent2.test')
chef_service = User.objects.get(identifiant='chef.service.test')
responsable_copec = User.objects.get(identifiant='responsable.copec.test')

agent.manager = chef_agence
agent.save()
agent2.manager = chef_agence
agent2.save()
chef_service.manager = responsable_copec
chef_service.save()

print('Données de test créées avec succès!')
"

echo ""
echo "✅ Configuration terminée !"
echo ""
echo "🚀 Pour démarrer le serveur :"
echo "   source venv/Scripts/activate"
echo "   python manage.py runserver"
echo ""
echo "📖 API Documentation :"
echo "   - POST /api/users/auth/login/ - Connexion"
echo "   - GET /api/missions/ - Liste des missions"
echo "   - POST /api/missions/ - Créer une mission"
echo "   - GET /api/users/profile/ - Profil utilisateur"
echo ""
echo "🔐 Comptes de test :"
echo "   - admin: admin / admin123"
echo "   - dg.test: password123"
echo "   - rh.test: password123"
echo "   - chef.service.test: password123"
echo "   - Autres comptes: password123"
