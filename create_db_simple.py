#!/usr/bin/env python
"""
Script simple pour créer la base PostgreSQL sans psycopg2
"""
import subprocess
import sys
import os

def run_sql_command(sql_command, dbname="postgres"):
    """Exécute une commande SQL via psql"""
    # Trouver le chemin de psql
    possible_paths = [
        r"C:\Program Files\PostgreSQL\16\bin\psql.exe",
        r"C:\Program Files\PostgreSQL\15\bin\psql.exe",
        r"C:\Program Files\PostgreSQL\14\bin\psql.exe",
        r"C:\Program Files\PostgreSQL\13\bin\psql.exe",
        "psql"
    ]

    psql_path = None
    for path in possible_paths:
        if os.path.exists(path) or path == "psql":
            psql_path = path
            break

    if not psql_path:
        print("❌ psql non trouvé")
        return False

    # Construire la commande
    cmd = [
        psql_path,
        "-U", "postgres",
        "-h", "localhost",
        "-p", "5432",
        "-d", dbname,
        "-c", sql_command
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, input="password\n")
        if result.returncode != 0:
            print(f"❌ Erreur SQL: {result.stderr}")
            return False
        print(f"✅ SQL exécuté: {sql_command}")
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    """Fonction principale"""
    print("🚀 Création de la base PostgreSQL 'fucec'")
    print("=" * 50)

    # Supprimer la base si elle existe
    print("🔍 Suppression de la base existante...")
    run_sql_command("DROP DATABASE IF EXISTS fucec;", "postgres")

    # Créer la base
    print("🔍 Création de la base 'fucec'...")
    success = run_sql_command("CREATE DATABASE fucec OWNER postgres ENCODING 'UTF8';", "postgres")

    if success:
        print("✅ Base de données 'fucec' créée avec succès !")
        print("📋 Vous pouvez maintenant lancer: python migrate_to_postgres.py")
        return True
    else:
        print("❌ Échec de la création de la base")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
