from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend

from .models import Mission, Validation, Justificatif
from .serializers import (
    MissionSerializer, MissionCreateSerializer,
    ValidationSerializer, JustificatifSerializer,
    JustificatifValidationSerializer,
    SignatureFinanciereSerializer, AvanceSerializer, NotificationSerializer
)
from .services import ValidationService, NotificationService, MissionReturnService


class MissionListView(generics.ListCreateAPIView):
    """Vue pour lister et créer des missions."""

    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['statut', 'type', 'createur']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MissionCreateSerializer
        return MissionSerializer

    def get_queryset(self):
        user = self.request.user

        # Filtrer selon la hiérarchie
        if user.role == 'ADMIN' or user.role == 'DG':
            # Admins et DG voient tout
            return Mission.objects.all()
        elif user.role == 'CHEF_AGENCE':
            # Chefs d'agence voient leurs missions et celles de leurs subordonnés
            subordinates = user.get_subordinates()
            subordinate_ids = [sub.id for sub in subordinates]
            return Mission.objects.filter(
                models.Q(createur=user) |
                models.Q(createur__in=subordinate_ids)
            )
        else:
            # Autres utilisateurs voient seulement leurs missions
            return Mission.objects.filter(createur=user)

    def perform_create(self, serializer):
        serializer.save(createur=self.request.user)


class MissionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vue pour récupérer, modifier et supprimer une mission."""

    serializer_class = MissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Même logique de filtrage que pour la liste
        user = self.request.user

        if user.role == 'ADMIN' or user.role == 'DG':
            return Mission.objects.all()
        elif user.role == 'CHEF_AGENCE':
            subordinates = user.get_subordinates()
            subordinate_ids = [sub.id for sub in subordinates]
            return Mission.objects.filter(
                models.Q(createur=user) |
                models.Q(createur__in=subordinate_ids)
            )
        else:
            return Mission.objects.filter(createur=user)


class ValidationListView(generics.ListCreateAPIView):
    """Vue pour lister et créer des validations."""

    serializer_class = ValidationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['statut', 'niveau', 'mission']

    def get_queryset(self):
        user = self.request.user

        if user.role == 'ADMIN' or user.role == 'DG':
            return Validation.objects.all()
        else:
            # Les utilisateurs voient les validations où ils sont valideurs
            return Validation.objects.filter(valideur=user)

    def perform_create(self, serializer):
        serializer.save(valideur=self.request.user)


class ValidationDetailView(generics.RetrieveUpdateAPIView):
    """Vue pour récupérer et mettre à jour une validation."""

    serializer_class = ValidationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role == 'ADMIN' or user.role == 'DG':
            return Validation.objects.all()
        else:
            return Validation.objects.filter(valideur=user)


class ValidateMissionView(APIView):
    """Vue pour valider ou rejeter une mission."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, mission_id, decision):
        try:
            mission = Mission.objects.get(id=mission_id)
            user = request.user

            # Vérifier que l'utilisateur peut valider cette mission
            if not mission.can_be_validated_by(user):
                return Response(
                    {'error': _('Vous n\'êtes pas autorisé à valider cette mission.')},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Vérifier que la mission est en attente de validation
            if mission.statut != 'EN_ATTENTE':
                return Response(
                    {'error': _('Cette mission n\'est pas en attente de validation.')},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Créer ou mettre à jour la validation
            validation, created = Validation.objects.get_or_create(
                mission=mission,
                valideur=user,
                defaults={'niveau': user.role}
            )

            # Mettre à jour la validation
            if decision.upper() == 'VALIDEE':
                validation.statut = 'VALIDEE'
                mission.statut = 'VALIDEE'
            elif decision.upper() == 'REJETEE':
                validation.statut = 'REJETEE'
                mission.statut = 'REJETEE'
            else:
                return Response(
                    {'error': _('Décision invalide. Utilisez "VALIDEE" ou "REJETEE".')},
                    status=status.HTTP_400_BAD_REQUEST
                )

            validation.commentaire = request.data.get('commentaire', '')
            validation.date_validation = timezone.now()
            validation.save()

            mission.save()

            return Response({
                'message': _(f'Mission {decision.lower()}e avec succès.'),
                'mission': MissionSerializer(mission, context={'request': request}).data
            })

        except Mission.DoesNotExist:
            return Response(
                {'error': _('Mission introuvable.')},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class JustificatifListView(generics.ListCreateAPIView):
    """Vue pour lister et créer des justificatifs."""

    serializer_class = JustificatifSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['statut', 'type', 'mission', 'intervenant']

    def get_queryset(self):
        user = self.request.user

        if user.role == 'ADMIN' or user.role == 'DG':
            return Justificatif.objects.all()
        elif user.can_validate:
            # Les validateurs voient les justificatifs de leur équipe
            if user.role == 'CHEF_AGENCE':
                team_members = [user.id] + [sub.id for sub in user.get_subordinates()]
                return Justificatif.objects.filter(intervenant__in=team_members)
            else:
                # Autres validateurs voient tout
                return Justificatif.objects.all()
        else:
            # Les intervenants voient seulement leurs justificatifs
            return Justificatif.objects.filter(intervenant=user)

    def perform_create(self, serializer):
        serializer.save(intervenant=self.request.user)


class JustificatifDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vue pour récupérer, modifier et supprimer un justificatif."""

    serializer_class = JustificatifSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role == 'ADMIN' or user.role == 'DG':
            return Justificatif.objects.all()
        elif user.can_validate:
            if user.role == 'CHEF_AGENCE':
                team_members = [user.id] + [sub.id for sub in user.get_subordinates()]
                return Justificatif.objects.filter(intervenant__in=team_members)
            else:
                return Justificatif.objects.all()
        else:
            return Justificatif.objects.filter(intervenant=user)


class ValidateJustificatifView(APIView):
    """Vue pour valider ou rejeter un justificatif."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, justificatif_id, decision):
        try:
            justificatif = Justificatif.objects.get(id=justificatif_id)
            user = request.user

            # Vérifier que l'utilisateur peut valider ce justificatif
            if not justificatif.peut_etre_valide_par(user):
                return Response(
                    {'error': _('Vous n\'êtes pas autorisé à valider ce justificatif.')},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Mettre à jour le justificatif
            if decision.upper() == 'VALIDER':
                justificatif.statut = 'VALIDE'
                justificatif.valideur = user
            elif decision.upper() == 'REJETER':
                justificatif.statut = 'REJETE'
                justificatif.valideur = user
            elif decision.upper() == 'REMBOURSER':
                justificatif.statut = 'REMBOURSE'
                justificatif.valideur = user
            else:
                return Response(
                    {'error': _('Décision invalide. Utilisez "VALIDER", "REJETER" ou "REMBOURSER".')},
                    status=status.HTTP_400_BAD_REQUEST
                )

            justificatif.commentaire_validation = request.data.get('commentaire', '')
            justificatif.date_validation = timezone.now()
            if decision.upper() == 'REMBOURSER':
                justificatif.date_remboursement = timezone.now()

            justificatif.save()

            return Response({
                'message': _(f'Justificatif {decision.lower()}é avec succès.'),
                'justificatif': JustificatifSerializer(justificatif, context={'request': request}).data
            })

        except Justificatif.DoesNotExist:
            return Response(
                {'error': _('Justificatif introuvable.')},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def mission_stats(request):
    """Vue pour obtenir les statistiques des missions."""
    user = request.user

    # Filtrer les missions selon les permissions
    if user.role == 'ADMIN' or user.role == 'DG':
        missions = Mission.objects.all()
    elif user.role == 'CHEF_AGENCE':
        subordinates = user.get_subordinates()
        subordinate_ids = [sub.id for sub in subordinates]
        missions = Mission.objects.filter(
            models.Q(createur=user) |
            models.Q(createur__in=subordinate_ids)
        )
    else:
        missions = Mission.objects.filter(createur=user)

    stats = {
        'total': missions.count(),
        'en_attente': missions.filter(statut='EN_ATTENTE').count(),
        'validees': missions.filter(statut='VALIDEE').count(),
        'en_cours': missions.filter(statut='EN_COURS').count(),
        'cloturees': missions.filter(statut='CLOTUREE').count(),
        'rejetees': missions.filter(statut='REJETEE').count(),
        'budget_total': sum(m.budget_prevu for m in missions),
    }

    return Response(stats)


class MissionSubmitView(APIView):
    """Vue pour soumettre une mission en validation."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            mission = Mission.objects.get(pk=pk)

            # Vérifier que l'utilisateur peut soumettre cette mission
            if mission.createur != request.user:
                return Response(
                    {'error': 'Vous ne pouvez soumettre que vos propres missions'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Vérifier que la mission est en brouillon
            if mission.statut != 'BROUILLON':
                return Response(
                    {'error': 'Seules les missions en brouillon peuvent être soumises'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Vérifier que la mission a tous les champs requis
            if not mission.entite or not mission.budget_estime:
                return Response(
                    {'error': 'La mission doit avoir une entité et un budget estimé'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Initier le workflow de validation
            validations = ValidationService.initiate_workflow(mission)

            serializer = MissionSerializer(mission)
            return Response({
                'message': 'Mission soumise avec succès',
                'mission': serializer.data,
                'validations_creees': len(validations)
            })

        except Mission.DoesNotExist:
            return Response(
                {'error': 'Mission non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )


class ValidationDecideView(APIView):
    """Vue pour prendre une décision sur une validation."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            validation = Validation.objects.get(pk=pk)

            # Vérifier que l'utilisateur est le valideur désigné
            if validation.valideur != request.user:
                return Response(
                    {'error': 'Vous n\'êtes pas autorisé à valider cette demande'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Vérifier que la validation est en attente
            if validation.statut != 'EN_ATTENTE':
                return Response(
                    {'error': 'Cette validation a déjà été traitée'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            decision = request.data.get('decision')
            commentaire = request.data.get('commentaire', '')

            if decision not in ['VALIDEE', 'REJETEE']:
                return Response(
                    {'error': 'Décision invalide. Utilisez VALIDEE ou REJETEE'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Traiter la décision
            validation = ValidationService.process_decision(validation, decision, commentaire)

            serializer = ValidationSerializer(validation)
            return Response({
                'message': f'Validation {decision.lower()}e avec succès',
                'validation': serializer.data
            })

        except Validation.DoesNotExist:
            return Response(
                {'error': 'Validation non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )


class ValidationListView(generics.ListAPIView):
    """Vue pour lister les validations."""

    serializer_class = ValidationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Filtrer selon le statut demandé
        statut_filter = self.request.query_params.get('statut', 'EN_ATTENTE')

        if user.role == 'ADMIN' or user.role == 'DG':
            # Admins et DG voient toutes les validations
            return Validation.objects.filter(statut=statut_filter)
        else:
            # Autres utilisateurs voient seulement leurs validations
            return Validation.objects.filter(valideur=user, statut=statut_filter)


class SignatureFinanciereView(APIView):
    """Vue pour gérer les signatures financières."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        from .models import SignatureFinanciere
        from .services import SignatureService

        try:
            signature = SignatureFinanciere.objects.get(pk=pk)

            # Vérifier que l'utilisateur est le signataire désigné
            if signature.signataire != request.user:
                return Response(
                    {'error': 'Vous n\'êtes pas autorisé à signer ce document'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Vérifier que la signature est en attente
            if signature.statut != 'EN_ATTENTE':
                return Response(
                    {'error': 'Cette signature a déjà été traitée'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Traiter la signature
            SignatureService.process_signature(signature)

            return Response({
                'message': 'Signature enregistrée avec succès'
            })

        except SignatureFinanciere.DoesNotExist:
            return Response(
                {'error': 'Signature non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )


class MissionDeclareReturnView(APIView):
    """Vue pour déclarer le retour de mission"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            mission = Mission.objects.get(pk=pk)

            # Vérifier que l'utilisateur est l'agent de la mission
            if mission.createur != request.user:
                return Response(
                    {'error': 'Seul l\'agent de la mission peut déclarer le retour'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Vérifier que la mission est en cours
            if mission.statut != 'EN_COURS':
                return Response(
                    {'error': 'La mission doit être en cours pour déclarer un retour'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Déclarer le retour
            mission = MissionReturnService.declare_return(mission, request.user)

            serializer = MissionSerializer(mission)
            return Response({
                'message': 'Retour de mission déclaré avec succès',
                'mission': serializer.data,
                'delai_justificatifs': mission.date_limite_justificatifs
            })

        except Mission.DoesNotExist:
            return Response(
                {'error': 'Mission non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class MissionSubmitJustificatifsView(APIView):
    """Vue pour soumettre les justificatifs de mission"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            mission = Mission.objects.get(pk=pk)

            # Vérifier que l'utilisateur est l'agent de la mission
            if mission.createur != request.user:
                return Response(
                    {'error': 'Seul l\'agent de la mission peut soumettre les justificatifs'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Vérifier que le retour a été déclaré
            if not mission.retour_declare:
                return Response(
                    {'error': 'Le retour de mission doit d\'abord être déclaré'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Soumettre les justificatifs (logique simplifiée)
            mission = MissionReturnService.submit_justificatifs(mission, request.data)

            serializer = MissionSerializer(mission)
            return Response({
                'message': 'Justificatifs soumis avec succès',
                'mission': serializer.data
            })

        except Mission.DoesNotExist:
            return Response(
                {'error': 'Mission non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )


class JustificatifVerifyView(APIView):
    """Vue pour vérifier les justificatifs (RH uniquement)"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            mission = Mission.objects.get(pk=pk)

            # Vérifier que l'utilisateur est RH
            if request.user.role != 'RH':
                return Response(
                    {'error': 'Seuls les utilisateurs RH peuvent vérifier les justificatifs'},
                    status=status.HTTP_403_FORBIDDEN
                )

            decision = request.data.get('decision')  # 'APPROUVE' ou 'REJETTE'
            commentaire = request.data.get('commentaire', '')

            if decision not in ['APPROUVE', 'REJETTE']:
                return Response(
                    {'error': 'Décision invalide. Utilisez APPROUVE ou REJETTE'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Vérifier les justificatifs
            MissionReturnService.verify_justificatifs(mission, request.user, decision, commentaire)

            serializer = MissionSerializer(mission)
            return Response({
                'message': f'Justificatifs {decision.lower()}és avec succès',
                'mission': serializer.data
            })

        except Mission.DoesNotExist:
            return Response(
                {'error': 'Mission non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )


class SignatureListView(generics.ListAPIView):
    """Vue pour lister les signatures en attente."""

    serializer_class = SignatureFinanciereSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        statut_filter = self.request.query_params.get('statut', 'EN_ATTENTE')

        return SignatureFinanciere.objects.filter(
            signataire=user,
            statut=statut_filter
        ).order_by('ordre')


class AvanceListCreateView(generics.ListCreateAPIView):
    """Vue pour lister et créer des avances."""

    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['mission', 'beneficiaire', 'statut']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AvanceCreateSerializer
        return AvanceSerializer

    def get_queryset(self):
        user = self.request.user

        # Les comptables voient toutes les avances
        if user.role == 'COMPTABLE':
            return Avance.objects.all()

        # Les autres voient seulement leurs avances (en tant que bénéficiaire)
        return Avance.objects.filter(beneficiaire=user)

    def perform_create(self, serializer):
        # Vérifier que l'utilisateur est comptable
        if self.request.user.role != 'COMPTABLE':
            raise serializers.ValidationError(
                "Seuls les comptables peuvent créer des avances."
            )

        # Vérifier que la mission a toutes les signatures
        mission = serializer.validated_data['mission']
        if not mission.signatures_completes:
            raise serializers.ValidationError(
                "La mission doit avoir toutes les signatures financières avant de verser une avance."
            )

        serializer.save(
            verse_par=self.request.user,
            beneficiaire=mission.createur  # L'agent est le bénéficiaire par défaut
        )


class AvanceDetailView(generics.RetrieveUpdateAPIView):
    """Vue pour consulter et mettre à jour une avance."""

    serializer_class = AvanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Les comptables voient toutes les avances
        if user.role == 'COMPTABLE':
            return Avance.objects.all()

        # Les autres voient seulement leurs avances
        return Avance.objects.filter(beneficiaire=user)

    def perform_update(self, serializer):
        # Seuls les comptables peuvent mettre à jour les avances
        if self.request.user.role != 'COMPTABLE':
            raise serializers.ValidationError(
                "Seuls les comptables peuvent modifier les avances."
            )

        # Mettre à jour le statut de la mission si nécessaire
        avance = self.instance
        new_statut = serializer.validated_data.get('statut')

        if new_statut == 'VERSEEE' and avance.statut != 'VERSEEE':
            # Notifier l'agent que l'avance a été versée
            NotificationService.notify_payment_made(avance.mission, avance)

        serializer.save()


class NotificationListView(generics.ListAPIView):
    """Vue pour lister les notifications de l'utilisateur."""

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(
            destinataire=self.request.user
        ).order_by('-date_creation')

    def list(self, request, *args, **kwargs):
        # Marquer toutes les notifications comme lues lors de la consultation
        Notification.objects.filter(
            destinataire=request.user,
            lue=False
        ).update(lue=True, date_lecture=timezone.now())

        return super().list(request, *args, **kwargs)


class SignatureListView(generics.ListAPIView):
    """Vue pour lister les signatures en attente."""

    serializer_class = SignatureFinanciereSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        statut_filter = self.request.query_params.get('statut', 'EN_ATTENTE')

        return SignatureFinanciere.objects.filter(
            signataire=user,
            statut=statut_filter
        ).order_by('ordre')


class AvanceListCreateView(generics.ListCreateAPIView):
    """Vue pour lister et créer des avances."""

    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['mission', 'beneficiaire', 'statut']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AvanceCreateSerializer
        return AvanceSerializer

    def get_queryset(self):
        user = self.request.user

        # Les comptables voient toutes les avances
        if user.role == 'COMPTABLE':
            return Avance.objects.all()

        # Les autres voient seulement leurs avances (en tant que bénéficiaire)
        return Avance.objects.filter(beneficiaire=user)

    def perform_create(self, serializer):
        # Vérifier que l'utilisateur est comptable
        if self.request.user.role != 'COMPTABLE':
            raise serializers.ValidationError(
                "Seuls les comptables peuvent créer des avances."
            )

        # Vérifier que la mission a toutes les signatures
        mission = serializer.validated_data['mission']
        if not mission.signatures_completes:
            raise serializers.ValidationError(
                "La mission doit avoir toutes les signatures financières avant de verser une avance."
            )

        serializer.save(
            verse_par=self.request.user,
            beneficiaire=mission.createur  # L'agent est le bénéficiaire par défaut
        )


class AvanceDetailView(generics.RetrieveUpdateAPIView):
    """Vue pour consulter et mettre à jour une avance."""

    serializer_class = AvanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Les comptables voient toutes les avances
        if user.role == 'COMPTABLE':
            return Avance.objects.all()

        # Les autres voient seulement leurs avances
        return Avance.objects.filter(beneficiaire=user)

    def perform_update(self, serializer):
        # Seuls les comptables peuvent mettre à jour les avances
        if self.request.user.role != 'COMPTABLE':
            raise serializers.ValidationError(
                "Seuls les comptables peuvent modifier les avances."
            )

        # Mettre à jour le statut de la mission si nécessaire
        avance = self.instance
        new_statut = serializer.validated_data.get('statut')

        if new_statut == 'VERSEEE' and avance.statut != 'VERSEEE':
            # Notifier l'agent que l'avance a été versée
            NotificationService.notify_payment_made(avance.mission, avance)

        serializer.save()


class NotificationListView(generics.ListAPIView):
    """Vue pour lister les notifications de l'utilisateur."""

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(
            destinataire=self.request.user
        ).order_by('-date_creation')

    def list(self, request, *args, **kwargs):
        # Marquer toutes les notifications comme lues lors de la consultation
        Notification.objects.filter(
            destinataire=request.user,
            lue=False
        ).update(lue=True, date_lecture=timezone.now())

        return super().list(request, *args, **kwargs)
