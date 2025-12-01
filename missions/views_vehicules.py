from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Vehicule
from .serializers import VehiculeSerializer, UserSerializer
from users.models import User

class VehiculeViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les véhicules.
    """
    queryset = Vehicule.objects.all()
    serializer_class = VehiculeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Les utilisateurs authentifiés peuvent voir tous les véhicules.
        Pour les utilisateurs avec le rôle CHAUFFEUR, on pourrait filtrer si nécessaire.
        """
        return Vehicule.objects.all()

    @action(detail=True, methods=['post'])
    def toggle_disponibilite(self, request, pk=None):
        """
        Bascule la disponibilité d'un véhicule.
        """
        vehicule = self.get_object()
        vehicule.disponible = not vehicule.disponible
        vehicule.save()
        return Response({
            'status': 'success',
            'message': f'Disponibilité du véhicule mise à jour: {vehicule.disponible}'
        })

class ChauffeurViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint pour gérer les chauffeurs.
    Les chauffeurs sont des utilisateurs avec le rôle CHAUFFEUR.
    """
    serializer_class = UserSerializer  # Utilisation directe de la classe UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Retourne uniquement les utilisateurs avec le rôle CHAUFFEUR
        from users.models import User, UserRole
        return User.objects.filter(role=UserRole.CHAUFFEUR)
    
    @action(detail=True, methods=['get'])
    def vehicules(self, request, pk=None):
        """
        Récupère les véhicules associés à un chauffeur.
        (À implémenter si vous avez une relation entre chauffeurs et véhicules)
        """
        return Response({
            'status': 'not_implemented',
            'message': 'Cette fonctionnalité n\'est pas encore implémentée.'
        }, status=status.HTTP_501_NOT_IMPLEMENTED)
