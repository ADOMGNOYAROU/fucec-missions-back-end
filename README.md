# FUCEC Missions Backend

Backend Django REST API pour le système de gestion des missions FUCEC.

## 🚀 Technologies Utilisées

- **Django 5.1.1** - Framework web Python
- **Django REST Framework** - API REST
- **Simple JWT** - Authentification JWT
- **PostgreSQL** - Base de données
- **django-cors-headers** - Gestion CORS
- **python-decouple** - Gestion des variables d'environnement

## 📋 Prérequis

- Python 3.8+
- PostgreSQL
- Git

## 🛠️ Installation

1. **Cloner le projet**
```bash
git clone <repository-url>
cd fucec-missions-backend
```

2. **Créer l'environnement virtuel**
```bash
python -m venv venv
source venv/Scripts/activate  # Windows
# ou
source venv/bin/activate     # Linux/Mac
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Configuration de la base de données**

   a. Créer une base de données PostgreSQL :
```sql
CREATE DATABASE fucec;
```

   b. Configurer les variables d'environnement :
```bash
cp .env.example .env
# Éditer .env avec vos paramètres PostgreSQL
```

5. **Configuration automatique**
```bash
chmod +x setup.sh
./setup.sh
```

Ou manuellement :
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

## 🐘 Migration vers PostgreSQL

### ⚠️ Prérequis PostgreSQL

Le système est maintenant configuré pour utiliser PostgreSQL. Assurez-vous que PostgreSQL est installé et configuré :

**Installation PostgreSQL :**
- **Windows** : Télécharger depuis https://www.postgresql.org/download/windows/
- **Ubuntu/Debian** : `sudo apt install postgresql postgresql-contrib`
- **macOS** : `brew install postgresql`

**Démarrage du service :**
- **Windows** : Ouvrir Services et démarrer 'postgresql-x64-XX'
- **Ubuntu/Debian** : `sudo systemctl start postgresql`
- **macOS** : `brew services start postgresql`

### 🔄 Migration depuis SQLite

Si vous aviez des données dans SQLite et souhaitez les migrer vers PostgreSQL :

1. **Vérifier PostgreSQL**
```bash
python setup_postgres.py
```

2. **Migrer les données**
```bash
python migrate_to_postgres.py
```

3. **Vérifier la migration**
```bash
python manage.py shell -c "from users.models import User; print(f'Utilisateurs: {User.objects.count()}')"
```

### 📝 Configuration .env pour PostgreSQL

```env
# Base de données PostgreSQL
DB_NAME=fucec
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432
```

## 🚀 Démarrage

```bash
source venv/Scripts/activate
python manage.py runserver
```

Le serveur sera accessible sur `http://localhost:8000`

## 📚 API Documentation

### Authentification

#### Connexion
```http
POST /api/users/auth/login/
Content-Type: application/json

{
  "identifiant": "chef.service.test",
  "password": "password123"
}
```

#### Rafraîchir le token
```http
POST /api/users/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "your_refresh_token"
}
```

### Missions

#### Lister les missions
```http
GET /api/missions/
Authorization: Bearer your_access_token
```

#### Créer une mission
```http
POST /api/missions/
Authorization: Bearer your_access_token
Content-Type: application/json

{
  "titre": "Mission de formation",
  "description": "Formation Angular avancé",
  "type": "FORMATION",
  "date_debut": "2025-01-15",
  "date_fin": "2025-01-17",
  "lieu_mission": "Lomé",
  "budget_prevu": 250000,
  "intervenants": [2, 8],
  "objet_mission": "Développement des compétences"
}
```

#### Valider une mission
```http
POST /api/missions/{id}/validate/validee/
Authorization: Bearer your_access_token
Content-Type: application/json

{
  "commentaire": "Mission approuvée"
}
```

### Justificatifs

#### Créer un justificatif
```http
POST /api/missions/justificatifs/
Authorization: Bearer your_access_token
Content-Type: application/json

{
  "mission": 1,
  "type": "TRANSPORT",
  "description": "Taxi aéroport",
  "montant": 15000,
  "devise": "XAF"
}
```

## 👥 Rôles Utilisateur

| Rôle | Permissions |
|------|-------------|
| **AGENT** | Créer ses missions, voir ses justificatifs |
| **CHEF_AGENCE** | Valider missions équipe, gérer justificatifs équipe |
| **RESPONSABLE_COPEC** | Valider missions, superviser services |
| **DG** | Accès complet, validation finale |
| **RH** | Gestion utilisateurs, validations RH |
| **COMPTABLE** | Gestion financière, validation budgets |
| **ADMIN** | Administration complète du système |

## 🔐 Comptes de Test

| Identifiant | Mot de passe | Rôle |
|-------------|-------------|------|
| admin | admin123 | ADMIN |
| dg.test | password123 | DG |
| rh.test | password123 | RH |
| chef.service.test | password123 | CHEF_AGENCE |
| agent.test | password123 | AGENT |

## 📁 Structure du Projet

```
fucec-missions-backend/
├── fucec_missions/          # Configuration Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── users/                   # Application utilisateurs
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── missions/                # Application missions
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── venv/                    # Environnement virtuel
├── requirements.txt
├── setup.sh                # Script de configuration
├── .env.example
└── README.md
```

## 🔗 Connexion Frontend

Le backend est configuré pour communiquer avec le frontend Angular sur :
- `http://localhost:4200`
- `http://127.0.0.1:4200`

## 📝 Logs et Debugging

Les logs sont configurés pour afficher :
- Requêtes API
- Erreurs d'authentification
- Opérations de validation
- Erreurs de base de données

## 🚀 Déploiement

Pour la production :
1. Configurer `DEBUG=False` dans `.env`
2. Utiliser un serveur WSGI (Gunicorn)
3. Configurer un reverse proxy (Nginx)
4. Sécuriser les variables d'environnement

## 📞 Support

Pour toute question ou problème, consultez :
- Documentation Django REST Framework
- Logs du serveur
- Tests unitaires
