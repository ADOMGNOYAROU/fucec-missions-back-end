"""
Tests de régression pour le workflow de mission/validation.

Couvre en particulier le bug critique corrigé dans ValidateMissionView
(AttributeError sur can_be_validated_by, statut 'EN_ATTENTE' inexistant,
champ 'validateur' au lieu de 'valideur') pour éviter toute régression.
"""
from datetime import date, timedelta

from rest_framework.test import APITestCase
from rest_framework import status

from users.models import User, UserRole
from .models import Mission, MissionStatus, Validation, ValidationStatus, ValidationNiveau


class MissionValidationWorkflowTests(APITestCase):
    def setUp(self):
        self.chef = User.objects.create_user(
            identifiant='chef.test', email='chef@fucec.cm',
            first_name='Chef', last_name='Agence',
            password='password123', role=UserRole.CHEF_AGENCE,
        )
        self.agent = User.objects.create_user(
            identifiant='agent.test', email='agent@fucec.cm',
            first_name='Agent', last_name='Un',
            password='password123', role=UserRole.AGENT, manager=self.chef,
        )
        self.mission = Mission.objects.create(
            titre='Formation Angular',
            description='Formation avancée',
            type='FORMATION',
            createur=self.agent,
            date_debut=date.today(),
            date_fin=date.today() + timedelta(days=2),
            lieu_mission='Lomé',
            budget_estime=250000,
        )

    def _create_pending_validation(self, valideur, niveau=ValidationNiveau.N_PLUS_1, ordre=1):
        return Validation.objects.create(
            mission=self.mission,
            valideur=valideur,
            niveau=niveau,
            ordre=ordre,
            statut=ValidationStatus.EN_ATTENTE,
        )

    def test_login_returns_jwt_tokens(self):
        response = self.client.post('/api/users/auth/login/', {
            'identifiant': 'agent.test',
            'password': 'password123',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_validate_mission_view_approves_when_validateur_authorized(self):
        validation = self._create_pending_validation(self.chef)

        self.client.force_authenticate(self.chef)
        response = self.client.post(
            f'/api/missions/missions/{self.mission.id}/validate/validee/',
            {'commentaire': 'OK pour moi'},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        validation.refresh_from_db()
        self.assertEqual(validation.statut, ValidationStatus.VALIDEE)

    def test_validate_mission_view_rejects_when_no_pending_validation(self):
        # Aucune Validation en attente pour cet utilisateur sur cette mission.
        self.client.force_authenticate(self.chef)
        response = self.client.post(
            f'/api/missions/missions/{self.mission.id}/validate/validee/',
            {'commentaire': 'OK'},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_validate_mission_view_rejette_la_mission(self):
        validation = self._create_pending_validation(self.chef)

        self.client.force_authenticate(self.chef)
        response = self.client.post(
            f'/api/missions/missions/{self.mission.id}/validate/rejettee/',
            {'commentaire': 'Budget trop élevé'},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        validation.refresh_from_db()
        self.mission.refresh_from_db()
        self.assertEqual(validation.statut, ValidationStatus.REJETEE)
        self.assertEqual(self.mission.statut, MissionStatus.REJETEE)

    def test_validation_decide_view_matches_validate_mission_view(self):
        """Les deux points d'entrée (legacy et nouveau) doivent produire le même résultat."""
        validation = self._create_pending_validation(self.chef)

        self.client.force_authenticate(self.chef)
        response = self.client.post(
            f'/api/missions/validations/{validation.id}/decide/',
            {'decision': 'VALIDEE', 'commentaire': 'Approuvé'},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        validation.refresh_from_db()
        self.assertEqual(validation.statut, ValidationStatus.VALIDEE)

    def test_validation_viewset_uses_valideur_field_not_validateur(self):
        """Régression : ValidationViewSet filtrait sur le champ inexistant 'validateur'."""
        self._create_pending_validation(self.chef)

        self.client.force_authenticate(self.chef)
        response = self.client.get('/api/missions/validations/')

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

    def test_mission_stats_endpoint(self):
        self.client.force_authenticate(self.agent)
        response = self.client.get('/api/missions/stats/')

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['total'], 1)
        self.assertEqual(int(response.data['budget_total']), 250000)
