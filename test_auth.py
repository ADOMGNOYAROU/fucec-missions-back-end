#!/usr/bin/env python
"""
Script de test d'authentification pour FUCEC Missions
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fucec_missions.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from users.models import User, UserRole
from rest_framework_simplejwt.tokens import AccessToken

def test_authentication():
    print('=== TEST D\'AUTHENTIFICATION JWT ===\n')

    # Tester chaque profil
    profiles_to_test = [
        ('admin', UserRole.ADMIN),
        ('dg', UserRole.DG),
        ('chef_agence', UserRole.CHEF_AGENCE),
        ('agent', UserRole.AGENT),
        ('rh', UserRole.RH),
        ('comptable', UserRole.COMPTABLE),
        ('chauffeur', UserRole.CHAUFFEUR),
        ('responsable_copec', UserRole.RESPONSABLE_COPEC),
        ('directeur_finances', UserRole.DIRECTEUR_FINANCES),
    ]

    successful_tests = 0

    for identifiant, expected_role in profiles_to_test:
        try:
            # Récupérer l'utilisateur
            user = User.objects.get(identifiant=identifiant)

            # Vérifier le rôle
            role_match = user.role == expected_role

            # Générer un token JWT
            token = AccessToken.for_user(user)

            # Vérifier les permissions
            permissions = {
                'can_validate': user.can_validate,
                'can_create_missions': user.can_create_missions,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
            }

            print(f'✅ {identifiant}:')
            print(f'   Rôle: {user.get_role_display()} ({role_match and "OK" or "ERREUR"})')
            print(f'   Token généré: {str(token)[:50]}...')
            print(f'   Permissions: {permissions}')
            print(f'   Actif: {user.is_active}')
            successful_tests += 1

        except User.DoesNotExist:
            print(f'❌ {identifiant}: UTILISATEUR INTROUVABLE')
        except Exception as e:
            print(f'❌ {identifiant}: ERREUR - {str(e)}')

        print()

    print('=== RÉCAPITULATIF ===')
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    print(f'Total utilisateurs: {total_users}')
    print(f'Utilisateurs actifs: {active_users}')
    print(f'Tests réussis: {successful_tests}/{len(profiles_to_test)}')

    print('\n=== RÉPARTITION PAR RÔLE ===')
    from django.db.models import Count
    role_counts = User.objects.values('role').annotate(count=Count('role')).order_by('role')
    for item in role_counts:
        role_display = dict(UserRole.choices)[item['role']]
        print(f'{role_display}: {item["count"]}')

    return successful_tests == len(profiles_to_test)

if __name__ == '__main__':
    success = test_authentication()
    sys.exit(0 if success else 1)
