#!/usr/bin/env python
"""
Guide de debug pour résoudre les problèmes d'authentification frontend
"""
print("🔧 GUIDE DE DEBUG AUTHENTIFICATION FRONTEND")
print("=" * 50)

print("\n📋 CHECKLIST DE DIAGNOSTIC:")
print("1. ✅ SERVEUR BACKEND ACTIF")
print("   - Vérifier: http://localhost:8000/api/users/auth/login/")
print("   - Devrait retourner JSON, pas HTML d'erreur")

print("\n2. ✅ AUTO-CONNEXION DEV ACTIVÉE")
print("   - Fichier: src/environments/environment.ts")
print("   - devAutoLogin: true ✅")
print("   - devUser configuré avec agent ✅")

print("\n3. ✅ SERVEUR ANGULAR DÉMARRÉ")
print("   Commande: cd frontend && npm start")
print("   URL: http://localhost:4200")

print("\n4. 🔍 DEBUG DANS LE NAVIGATEUR")
print("   - Ouvrir: http://localhost:4200")
print("   - F12 → Console pour voir les logs")
print("   - Chercher: 'AuthService', 'auto-connexion', 'token'")

print("\n5. 🔍 VÉRIFIER LOCALSTORAGE")
print("   Dans la console du navigateur:")
print("   localStorage.getItem('access_token')")
print("   localStorage.getItem('current_user')")
print("   localStorage.getItem('refresh_token')")

print("\n6. 🔍 TEST DES GUARDS")
print("   - Aller sur: http://localhost:4200/missions")
print("   - Si redirection login → problème de guard")
print("   - Vérifier console pour erreurs")

print("\n🚨 PROBLÈMES POSSIBLES:")

print("\n   A) SERVEUR ANGULAR PAS DÉMARRÉ")
print("   ✅ Solution: npm start dans dossier frontend")

print("\n   B) AUTO-CONNEXION NE FONCTIONNE PAS")
print("   ✅ Vérifier: environment.ts → devAutoLogin: true")
print("   ✅ Vérifier: devUser.role = UserRole.AGENT")

print("\n   C) GUARDS TROP RESTRICTIFS")
print("   ✅ missions.routes.ts: roleGuard([UserRole.AGENT, UserRole.CHEF_AGENCE])")

print("\n   D) TOKENS EXPIRÉS")
print("   ✅ Vérifier expiration JWT (1 heure)")
print("   ✅ Rafraîchissement automatique configuré")

print("\n   E) CORS OU API URL")
print("   ✅ environment.ts: apiUrl: 'http://localhost:8000/api'")
print("   ✅ Backend CORS configuré pour localhost:4200")

print("\n🔧 COMMANDES DE TEST:")

print("\n# Test backend API:")
print('curl -X POST http://localhost:8000/api/users/auth/login/ \\')
print('  -H "Content-Type: application/json" \\')
print('  -d \'{"identifiant":"agent","password":"test123"}\'')

print("\n# Test création mission:")
print('TOKEN=$(curl -s -X POST http://localhost:8000/api/users/auth/login/ \\')
print('  -H "Content-Type: application/json" \\')
print('  -d \'{"identifiant":"agent","password":"test123"}\' | jq -r .access)')
print("")
print('curl -X POST http://localhost:8000/api/missions/ \\')
print('  -H "Authorization: Bearer $TOKEN" \\')
print('  -H "Content-Type: application/json" \\')
print('  -d \'{"titre":"Test","description":"Test","type":"FORMATION","date_debut":"2025-12-15","date_fin":"2025-12-16","lieu_mission":"Test","budget_estime":100000,"avance_demandee":50000}\'')

print("\n🎯 PROCÉDURE DE RÉSOLUTION:")

print("\n1. Arrêter tous les serveurs (Ctrl+C)")
print("2. Redémarrer backend: python manage.py runserver")
print("3. Dans nouveau terminal: cd frontend && npm start")
print("4. Ouvrir http://localhost:4200")
print("5. Vérifier console navigateur (F12)")
print("6. Tester navigation vers /missions/create-order")

print("\n📞 SI PROBLÈME PERSISTE:")
print("- Fournir les logs de la console navigateur")
print("- Indiquer l'URL exacte qui pose problème")
print("- Préciser le comportement observé")

print("\n✅ SYSTÈME FONCTIONNEL QUAND:")
print("- Auto-connexion dev fonctionne au démarrage")
print("- Navigation vers missions sans redirection login")
print("- Formulaire de création accessible et fonctionnel")
