"""
Permissions personnalisées pour l'application missions
"""
from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """Permission: Admin peut tout faire, autres peuvent seulement lire."""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_authenticated and request.user.role == 'ADMIN'


class IsAdminOrDG(permissions.BasePermission):
    """Permission: Seuls Admin et DG ont accès."""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['ADMIN', 'DG']
        )


class IsAdminOrRH(permissions.BasePermission):
    """Permission: Seuls Admin et RH ont accès."""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['ADMIN', 'RH']
        )


class IsAdminOrComptable(permissions.BasePermission):
    """Permission: Seuls Admin et Comptable ont accès."""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['ADMIN', 'COMPTABLE']
        )


class IsChefAgenceOrAbove(permissions.BasePermission):
    """Permission: Chef d'agence et rôles supérieurs."""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['ADMIN', 'DG', 'CHEF_AGENCE', 'RESPONSABLE_COPEC']
        )


class CanManageBudget(permissions.BasePermission):
    """Permission: Peut gérer les budgets (Admin, DG, Directeur Finances)."""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['ADMIN', 'DG', 'DIRECTEUR_FINANCES', 'COMPTABLE']
        )


class CanManageService(permissions.BasePermission):
    """Permission: Peut gérer les services (Admin, DG, RH)."""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['ADMIN', 'DG', 'RH']
        )


class CanManageDelegation(permissions.BasePermission):
    """Permission: Peut gérer les délégations."""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Seuls les managers peuvent créer des délégations
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.role in ['ADMIN', 'DG', 'CHEF_AGENCE', 'RESPONSABLE_COPEC'] or
             request.user.get_subordinates().exists())
        )
    
    def has_object_permission(self, request, view, obj):
        # L'utilisateur peut voir/modifier ses propres délégations
        if request.user == obj.delegant or request.user == obj.delegataire:
            return True
        
        # Admin et DG peuvent tout voir
        if request.user.role in ['ADMIN', 'DG']:
            return True
        
        return False


class CanValidateMission(permissions.BasePermission):
    """Permission: Peut valider des missions."""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'can_validate') and 
            request.user.can_validate
        )
    
    def has_object_permission(self, request, view, obj):
        # Vérifier si l'utilisateur peut valider cette mission spécifique
        if hasattr(obj, 'can_be_validated_by'):
            return obj.can_be_validated_by(request.user)
        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Permission: Le propriétaire peut modifier, les autres seulement lire."""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Vérifier si l'objet a un attribut 'createur' ou 'intervenant'
        if hasattr(obj, 'createur'):
            return obj.createur == request.user
        elif hasattr(obj, 'intervenant'):
            return obj.intervenant == request.user
        
        return False


class CanManageVehicule(permissions.BasePermission):
    """Permission: Peut gérer les véhicules."""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['ADMIN', 'DG', 'RH', 'RESPONSABLE_COPEC']
        )
