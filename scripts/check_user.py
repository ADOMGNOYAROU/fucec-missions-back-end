#!/usr/bin/env python3
"""
Script pour vérifier/créer l'utilisateur de test
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fucec_missions.settings')
django.setup()

from users.models import User

def main():
    print("🔍 Vérification de l'utilisateur de test...")

    try:
        user = User.objects.get(identifiant='agent1')
        print(f"✅ Utilisateur trouvé: {user}")
        print(f"   - Prénom: {user.first_name}")
        print(f"   - Nom: {user.last_name}")
        print(f"   - Rôle: {user.role}")
        print(f"   - Actif: {user.is_active}")
        print(f"   - Mot de passe valide: {user.check_password('password123')}")

    except User.DoesNotExist:
        print("❌ Utilisateur agent1 n'existe pas - création...")
        try:
            user = User.objects.create_user(
                identifiant='agent1',
                email='agent1@example.com',
                password='password123',
                first_name='Test',
                last_name='Agent',
                role='AGENT'
            )
            print(f"✅ Utilisateur créé: {user}")
        except Exception as e:
            print(f"❌ Erreur lors de la création: {e}")
            return False

    print("\n🔍 Vérification terminée")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
