#!/usr/bin/env python
"""
Vérification et configuration de PostgreSQL pour FUCEC
"""
import subprocess
import sys

def run_command(cmd, check=True):
    """Exécute une commande et retourne le résultat"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if check and result.returncode != 0:
            print(f"❌ Erreur: {result.stderr}")
            return False, result.stderr
        return True, result.stdout.strip()
    except Exception as e:
        return False, str(e)

def check_postgresql():
    """Vérifie si PostgreSQL est installé et accessible"""
    print("🔍 Vérification de PostgreSQL...")

    # Vérifier si psql est disponible
    success, output = run_command("psql --version", check=False)
    if not success:
        print("❌ PostgreSQL n'est pas installé")
        print("📋 Installation de PostgreSQL requise:")
        print("   - Windows: Télécharger depuis https://www.postgresql.org/download/windows/")
        print("   - Ubuntu/Debian: sudo apt install postgresql postgresql-contrib")
        print("   - macOS: brew install postgresql")
        return False

    print(f"✅ PostgreSQL détecté: {output}")

    # Vérifier si le service est démarré
    success, output = run_command("pg_isready -h localhost -p 5432", check=False)
    if not success:
        print("❌ Le service PostgreSQL n'est pas démarré")
        print("📋 Démarrage du service PostgreSQL:")
        print("   - Windows: Ouvrir Services et démarrer 'postgresql-x64-XX'")
        print("   - Ubuntu/Debian: sudo systemctl start postgresql")
        print("   - macOS: brew services start postgresql")
        return False

    print("✅ Service PostgreSQL démarré")

    # Tester la connexion avec Python
    try:
        import psycopg2
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="password",
            host="localhost",
            port="5432"
        )
        conn.close()
        print("✅ Connexion PostgreSQL réussie")
        return True
    except ImportError:
        print("❌ psycopg2 n'est pas installé")
        print("📋 Installer avec: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

def create_database():
    """Crée la base de données 'fucec'"""
    print("🔍 Création de la base de données 'fucec'...")

    try:
        import psycopg2

        # Se connecter à postgres pour créer la base
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="password",
            host="localhost",
            port="5432"
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Supprimer la base si elle existe
        cursor.execute("DROP DATABASE IF EXISTS fucec;")

        # Créer la base de données
        cursor.execute("CREATE DATABASE fucec OWNER postgres ENCODING 'UTF8';")

        cursor.close()
        conn.close()

        print("✅ Base de données 'fucec' créée avec succès")
        return True

    except Exception as e:
        print(f"❌ Erreur lors de la création: {e}")
        return False

def main():
    """Fonction principale"""
    print("🚀 Configuration PostgreSQL pour FUCEC")
    print("=" * 50)

    if not check_postgresql():
        return False

    if not create_database():
        return False

    print("✅ Configuration PostgreSQL terminée !")
    print("📋 Prochaines étapes:")
    print("   1. Installer les dépendances: pip install -r requirements.txt")
    print("   2. Lancer la migration: python migrate_to_postgres.py")
    print("   3. Tester: python manage.py runserver")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
