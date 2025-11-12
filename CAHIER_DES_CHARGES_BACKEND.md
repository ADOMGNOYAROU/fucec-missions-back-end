# Cahier des Charges - Backend FUCEC Missions

## 1. PRÉSENTATION GÉNÉRALE

### 1.1 Contexte
Le système FUCEC Missions est une plateforme digitale de gestion des missions et justificatifs pour l'organisation FUCEC. Il permet aux employés de créer et soumettre des demandes de mission, aux validateurs de les approuver selon une hiérarchie définie, et aux services financiers de gérer les remboursements.

### 1.2 Objectifs
- **Numérisation** : Remplacer les processus papier par un système numérique
- **Efficacité** : Automatiser les workflows de validation et de remboursement
- **Transparence** : Fournir une visibilité complète sur le statut des missions
- **Sécurité** : Garantir la confidentialité des données et l'intégrité des processus

---

## 2. ARCHITECTURE TECHNIQUE

### 2.1 Technologies Utilisées

#### Backend
- **Framework** : Django 5.1.1
- **API REST** : Django REST Framework 3.15.1
- **Authentification** : JWT (djangorestframework-simplejwt 5.3.1)
- **Base de données** : PostgreSQL 15+
- **Filtrage** : django-filter 23.5
- **Gestion des images** : Pillow 10.3.0
- **CORS** : django-cors-headers 4.3.1
- **Configuration** : python-decouple 3.8

#### Sécurité
- Authentification JWT avec rotation des tokens
- Autorisations basées sur les rôles utilisateur
- Validation des permissions par endpoint
- Gestion des sessions sécurisée

#### Configuration
- Variables d'environnement pour la configuration
- Support du développement et production
- Logging intégré
- Gestion des fichiers statiques

---

## 3. MODÈLE DE DONNÉES

### 3.1 Utilisateurs (`users.User`)

#### Champs principaux
- `identifiant` : Identifiant unique (USERNAME_FIELD)
- `nom`, `prenom` : Nom complet
- `email` : Adresse email
- `role` : Rôle dans l'organisation
- `manager` : Manager hiérarchique
- `telephone`, `matricule` : Informations complémentaires
- `entite_nom`, `entite_type` : Appartenance organisationnelle

#### Rôles définis
```python
class UserRole(models.TextChoices):
    AGENT = 'AGENT'                    # Agent de base
    CHEF_AGENCE = 'CHEF_AGENCE'         # Chef d'agence
    RESPONSABLE_COPEC = 'RESPONSABLE_COPEC'  # Responsable COPEC
    DG = 'DG'                         # Directeur Général
    RH = 'RH'                         # Ressources Humaines
    COMPTABLE = 'COMPTABLE'           # Comptable
    ADMIN = 'ADMIN'                   # Administrateur
    DIRECTEUR_FINANCES = 'DIRECTEUR_FINANCES'  # Directeur Finances
    CHAUFFEUR = 'CHAUFFEUR'           # Chauffeur
```

#### Permissions par rôle
| Rôle | Créer missions | Valider missions | Gérer utilisateurs | Voir tout |
|------|---------------|------------------|-------------------|-----------|
| AGENT | ✓ | ✗ | ✗ | ✗ |
| CHEF_AGENCE | ✓ | Équipe | Équipe | ✗ |
| RESPONSABLE_COPEC | ✓ | ✓ | ✗ | ✗ |
| DG | ✓ | ✓ | ✗ | ✓ |
| RH | ✓ | ✓ | ✓ | ✗ |
| COMPTABLE | ✓ | ✓ | ✗ | ✗ |
| ADMIN | ✓ | ✓ | ✓ | ✓ |

### 3.2 Missions (`missions.Mission`)

#### Champs principaux
- `titre` : Titre descriptif
- `description` : Description détaillée
- `type` : Type de mission (Formation, Réunion, Commercial, Audit, Autre)
- `statut` : Statut actuel (Brouillon, En attente, Validée, En cours, Clôturée, Rejetée)
- `date_debut`, `date_fin` : Période de la mission
- `lieu_mission` : Lieu de déroulement
- `budget_prevu` : Budget alloué (FCFA)
- `createur` : Utilisateur créateur
- `valideur_actuel` : Validateur en cours
- `intervenants` : Participants (relation ManyToMany)

#### Types de mission
```python
class MissionType(models.TextChoices):
    FORMATION = 'FORMATION'
    REUNION = 'REUNION'
    MISSION_COMMERCIALE = 'MISSION_COMMERCIALE'
    AUDIT = 'AUDIT'
    AUTRE = 'AUTRE'
```

#### Statuts de mission
```python
class MissionStatus(models.TextChoices):
    BROUILLON = 'BROUILLON'
    EN_ATTENTE = 'EN_ATTENTE'
    VALIDEE = 'VALIDEE'
    EN_COURS = 'EN_COURS'
    CLOTUREE = 'CLOTUREE'
    REJETEE = 'REJETEE'
```

### 3.3 Validations (`missions.Validation`)

#### Champs principaux
- `mission` : Mission concernée
- `valideur` : Utilisateur validateur
- `niveau` : Niveau de validation (Chef agence, COPEC, DG, RH)
- `statut` : Statut de validation (En attente, Validée, Rejetée)
- `commentaire` : Commentaire du valideur
- `date_creation`, `date_validation` : Dates importantes

#### Niveaux de validation
```python
class ValidationNiveau(models.TextChoices):
    CHEF_AGENCE = 'CHEF_AGENCE'
    RESPONSABLE_COPEC = 'RESPONSABLE_COPEC'
    DG = 'DG'
    RH = 'RH'
```

### 3.4 Justificatifs (`missions.Justificatif`)

#### Champs principaux
- `mission` : Mission associée
- `intervenant` : Utilisateur concerné
- `type` : Type de dépense (Transport, Hébergement, Restauration, Autre)
- `description`, `categorie` : Détails de la dépense
- `montant`, `devise` : Montant en devise (défaut XAF)
- `statut` : Statut du justificatif (En attente, Validé, Rejeté, Remboursé)
- `fichier` : Justificatif scanné/photo (optionnel)
- `valideur` : Utilisateur validateur
- `commentaire_validation` : Commentaire de validation

#### Types de justificatif
```python
class JustificatifType(models.TextChoices):
    TRANSPORT = 'TRANSPORT'
    HEBERGEMENT = 'HEBERGEMENT'
    RESTAURATION = 'RESTAURATION'
    AUTRE = 'AUTRE'
```

#### Statuts de justificatif
```python
class JustificatifStatus(models.TextChoices):
    EN_ATTENTE = 'EN_ATTENTE'
    VALIDE = 'VALIDE'
    REJETE = 'REJETE'
    REMBOURSE = 'REMBOURSE'
```

---

## 4. API REST

### 4.1 Authentification (`/api/users/auth/`)

#### POST `/api/users/auth/login/`
**Connexion utilisateur**
```json
{
  "identifiant": "chef.service.test",
  "password": "password123"
}
```

**Réponse :**
```json
{
  "refresh": "jwt_refresh_token",
  "access": "jwt_access_token",
  "user": { "id": 1, "identifiant": "...", "role": "..." },
  "message": "Connexion réussie"
}
```

#### POST `/api/users/auth/token/refresh/`
**Rafraîchir le token d'accès**
```json
{
  "refresh": "jwt_refresh_token"
}
```

#### POST `/api/users/auth/logout/`
**Déconnexion**
```json
{
  "refresh_token": "jwt_refresh_token"
}
```

### 4.2 Gestion des utilisateurs (`/api/users/`)

#### GET `/api/users/profile/`
**Récupérer le profil utilisateur**

#### PUT `/api/users/profile/`
**Mettre à jour le profil**

#### POST `/api/users/profile/change-password/`
**Changer le mot de passe**
```json
{
  "old_password": "ancien_mot_de_passe",
  "new_password": "nouveau_mot_de_passe"
}
```

#### GET `/api/users/users/`
**Lister les utilisateurs** (selon permissions)

#### GET `/api/users/users/subordinates/`
**Lister les subordonnés**

### 4.3 Gestion des missions (`/api/missions/`)

#### GET `/api/missions/`
**Lister les missions**
- **Filtres** : `statut`, `type`, `createur`
- **Permissions** : Selon hiérarchie

#### POST `/api/missions/`
**Créer une mission**
```json
{
  "titre": "Formation Angular",
  "description": "Formation avancée Angular",
  "type": "FORMATION",
  "date_debut": "2025-01-15",
  "date_fin": "2025-01-17",
  "lieu_mission": "Lomé",
  "budget_prevu": 250000,
  "intervenants": [2, 8],
  "objet_mission": "Développement compétences"
}
```

#### GET `/api/missions/{id}/`
**Détails d'une mission**

#### PUT `/api/missions/{id}/`
**Modifier une mission**

#### DELETE `/api/missions/{id}/`
**Supprimer une mission**

#### POST `/api/missions/{id}/validate/{decision}/`
**Valider/Rejeter une mission**
- `decision` : `validee` ou `rejettee`
```json
{
  "commentaire": "Mission approuvée"
}
```

#### GET `/api/missions/validations/`
**Lister les validations**

#### GET `/api/missions/validations/{id}/`
**Détails d'une validation**

#### GET `/api/missions/stats/`
**Statistiques des missions**
```json
{
  "total": 45,
  "en_attente": 12,
  "validees": 25,
  "en_cours": 3,
  "cloturees": 4,
  "rejetees": 1,
  "budget_total": 15000000
}
```

### 4.4 Gestion des justificatifs (`/api/missions/justificatifs/`)

#### GET `/api/missions/justificatifs/`
**Lister les justificatifs**
- **Filtres** : `statut`, `type`, `mission`, `intervenant`

#### POST `/api/missions/justificatifs/`
**Créer un justificatif**
```json
{
  "mission": 1,
  "type": "TRANSPORT",
  "description": "Taxi aéroport",
  "montant": 15000,
  "devise": "XAF"
}
```

#### GET `/api/missions/justificatifs/{id}/`
**Détails d'un justificatif**

#### PUT `/api/missions/justificatifs/{id}/`
**Modifier un justificatif**

#### DELETE `/api/missions/justificatifs/{id}/`
**Supprimer un justificatif**

#### POST `/api/missions/justificatifs/{id}/validate/{decision}/`
**Valider/Rejeter/Rembourser un justificatif**
- `decision` : `valider`, `rejeter`, `rembourser`
```json
{
  "commentaire": "Justificatif validé"
}
```

---

## 5. WORKFLOWS MÉTIER

### 5.1 Processus de création de mission

1. **Création par l'agent**
   - Agent crée la mission en brouillon
   - Définit titre, description, dates, budget, intervenants
   - Soumet pour validation

2. **Validation hiérarchique**
   - **Chef d'agence** : Valide les missions de son équipe
   - **Responsable COPEC** : Valide selon les politiques
   - **Directeur Général** : Validation finale pour montants élevés

3. **Exécution**
   - Mission passe en statut "En cours"
   - Intervenants peuvent soumettre des justificatifs

4. **Clôture**
   - Mission terminée, justificatifs validés
   - Remboursements effectués

### 5.2 Processus de validation des justificatifs

1. **Soumission**
   - Intervenant soumet justificatif avec preuve (photo/scan)

2. **Validation**
   - **Chef d'agence** : Valide justificatifs de son équipe
   - **Responsable COPEC** : Valide selon politiques
   - **Comptable** : Vérification comptable
   - **Directeur Finances** : Validation budgétaire

3. **Remboursement**
   - Justificatif marqué "Remboursé"
   - Paiement effectué

---

## 6. SÉCURITÉ ET AUTORISATIONS

### 6.1 Authentification
- JWT avec access token (1h) et refresh token (7 jours)
- Rotation automatique des tokens
- Blacklist des tokens révoqués

### 6.2 Autorisations
- Permissions basées sur les rôles utilisateur
- Vérification des droits par endpoint
- Filtrage des données selon la hiérarchie

### 6.3 Validation des données
- Validation côté serveur pour tous les champs
- Contraintes d'intégrité référentielle
- Validation métier (dates, montants, hiérarchie)

---

## 7. DÉPLOIEMENT ET INFRASTRUCTURE

### 7.1 Environnements
- **Développement** : Configuration locale avec DEBUG=True
- **Production** : Configuration sécurisée avec DEBUG=False

### 7.2 Prérequis système
- Python 3.8+
- PostgreSQL 15+
- Serveur web (Nginx recommandé)
- WSGI server (Gunicorn recommandé)

### 7.3 Configuration
```bash
# Variables d'environnement (.env)
SECRET_KEY=your-secret-key
DEBUG=False
DB_NAME=fucec_missions
DB_USER=postgres
DB_PASSWORD=secure-password
DB_HOST=localhost
DB_PORT=5432
ALLOWED_HOSTS=your-domain.com
CORS_ALLOWED_ORIGINS=https://your-frontend.com
```

### 7.4 Commandes de déploiement
```bash
# Installation
pip install -r requirements.txt
python manage.py collectstatic
python manage.py migrate

# Lancement
gunicorn fucec_missions.wsgi:application --bind 0.0.0.0:8000
```

---

## 8. MAINTENANCE ET ÉVOLUTION

### 8.1 Monitoring
- Logs Django intégrés
- Métriques de performance des API
- Suivi des erreurs et exceptions

### 8.2 Sauvegarde
- Sauvegarde automatique de la base PostgreSQL
- Archival des fichiers justificatifs
- Rétention des données selon politique

### 8.3 Évolutivité
- Architecture modulaire (apps Django séparées)
- API REST extensible
- Support des migrations de base de données

---

## 9. TESTS ET QUALITÉ

### 9.1 Tests unitaires
- Tests des modèles et méthodes métier
- Tests des serializers et validations
- Tests des vues et permissions

### 9.2 Tests d'intégration
- Tests des workflows complets
- Tests des API endpoints
- Tests de sécurité

### 9.3 Données de test
Comptes de test prédéfinis :
- `admin` / `admin123` (ADMIN)
- `dg.test` / `password123` (DG)
- `rh.test` / `password123` (RH)
- `chef.service.test` / `password123` (CHEF_AGENCE)
- `agent.test` / `password123` (AGENT)

---

## 10. ANNEXES

### 10.1 Schéma de base de données
```
Users
├── id (PK)
├── identifiant (unique)
├── role
├── manager (FK → Users)
├── entite_nom
└── autres champs...

Missions
├── id (PK)
├── titre
├── type
├── statut
├── createur (FK → Users)
├── valideur_actuel (FK → Users)
├── budget_prevu
└── autres champs...

Validations
├── id (PK)
├── mission (FK → Missions)
├── valideur (FK → Users)
├── niveau
├── statut
└── autres champs...

Justificatifs
├── id (PK)
├── mission (FK → Missions)
├── intervenant (FK → Users)
├── type
├── montant
├── statut
└── autres champs...
```

### 10.2 Codes d'erreur API
- `400` : Données invalides
- `401` : Non authentifié
- `403` : Permissions insuffisantes
- `404` : Ressource non trouvée
- `500` : Erreur serveur

### 10.3 Formats de données
- **Dates** : `YYYY-MM-DD`
- **Montants** : Décimal avec 2 décimales
- **Devise** : Code ISO (XAF par défaut)
- **Images** : JPEG, PNG, formats standard

---

*Ce cahier des charges définit complètement l'architecture et les fonctionnalités du backend FUCEC Missions. Il sert de référence pour le développement, les tests et la maintenance du système.*
