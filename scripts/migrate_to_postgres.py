#!/usr/bin/env python
"""
Script pour migrer de SQLite vers PostgreSQL
"""
import os
import sys
import sqlite3
import subprocess
from pathlib import Path

# Ajouter le répertoire du projet au path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

def run_command(cmd, cwd=None):
    """Exécute une commande et retourne le résultat"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Erreur lors de l'exécution de '{cmd}': {result.stderr}")
            return False
        print(f"✅ Commande exécutée: {cmd}")
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def create_postgres_db():
    """Crée la base de données PostgreSQL"""
    print("🔍 Création de la base de données PostgreSQL 'fucec'...")

    # Commandes SQL pour créer la base de données
    sql_commands = [
        "DROP DATABASE IF EXISTS fucec;",
        "CREATE DATABASE fucec OWNER postgres ENCODING 'UTF8';",
        "GRANT ALL PRIVILEGES ON DATABASE fucec TO postgres;"
    ]

    # Créer un script temporaire pour créer la base
    create_db_script = BASE_DIR / "create_db.sql"
    with open(create_db_script, 'w') as f:
        f.write("\\c postgres\n")
        for cmd in sql_commands:
            f.write(f"{cmd}\n")

    try:
        # Exécuter le script avec psql
        success = run_command(f'psql -U postgres -f "{create_db_script}"')
        if success:
            print("✅ Base de données PostgreSQL 'fucec' créée avec succès")
        return success
    finally:
        # Nettoyer le fichier temporaire
        if create_db_script.exists():
            create_db_script.unlink()

def migrate_data():
    """Migre les données de SQLite vers PostgreSQL"""
    print("🔍 Migration des données de SQLite vers PostgreSQL...")

    # Créer un fichier temporaire avec la configuration SQLite
    sqlite_settings = """
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
"""

    postgres_settings = """
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'fucec',
        'USER': 'postgres',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
"""

    # Étape 1: Créer les migrations avec SQLite
    print("🔄 Étape 1: Création des migrations...")
    success = run_command("py manage.py makemigrations", cwd=BASE_DIR)
    if not success:
        return False

    # Étape 2: Appliquer les migrations sur PostgreSQL
    print("🔄 Étape 2: Application des migrations sur PostgreSQL...")
    success = run_command("py manage.py migrate", cwd=BASE_DIR)
    if not success:
        return False

    print("✅ Migration terminée avec succès")
    return True

def main():
    """Fonction principale"""
    print("🚀 Migration SQLite vers PostgreSQL")
    print("=" * 50)

    # Vérifier que PostgreSQL est installé et accessible
    print("🔍 Vérification de PostgreSQL...")
    if not run_command("psql --version"):
        print("❌ PostgreSQL n'est pas installé ou accessible")
        print("📋 Veuillez installer PostgreSQL et créer l'utilisateur 'postgres'")
        return False

    # Vérifier que le service PostgreSQL est démarré
    print("🔍 Vérification du service PostgreSQL...")
    if not run_command("pg_isready -h localhost -p 5432"):
        print("❌ Le service PostgreSQL n'est pas démarré")
        print("📋 Veuillez démarrer PostgreSQL")
        return False

    # Créer la base de données
    if not create_postgres_db():
        return False

    # Migrer les données
    if not migrate_data():
        return False

    # Vérifier la migration
    print("🔍 Vérification de la migration...")
    success = run_command("py manage.py shell -c \"from users.models import User; print(f'Utilisateurs migrés: {User.objects.count()}')\"", cwd=BASE_DIR)

    if success:
        print("✅ Migration complète réussie !")
        print("📋 Pensez à mettre à jour votre fichier .env avec les variables PostgreSQL:")
        print("   DB_NAME=fucec")
        print("   DB_USER=postgres")
        print("   DB_PASSWORD=password")
        print("   DB_HOST=localhost")
        print("   DB_PORT=5432")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
