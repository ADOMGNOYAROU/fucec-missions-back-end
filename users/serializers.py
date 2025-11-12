from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from .models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class UserSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle User."""

    manager = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), allow_null=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'identifiant', 'first_name', 'last_name', 'email', 
            'role', 'manager', 'telephone', 'matricule', 'entite', 
            'agence', 'service', 'direction'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création d'utilisateurs."""

    password = serializers.CharField(write_only=True, required=True)
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'identifiant', 'first_name', 'last_name', 'email', 'role',
            'manager', 'telephone', 'matricule', 'password', 'password_confirm'
        ]

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError(_("Les mots de passe ne correspondent pas."))
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer pour la connexion utilisateur."""

    identifiant = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        identifiant = data.get('identifiant')
        password = data.get('password')

        if identifiant and password:
            # Utiliser User.objects.get() au lieu d'authenticate() pour les modèles personnalisés
            try:
                user = User.objects.get(identifiant=identifiant)
                if user.check_password(password):
                    if user.is_active:
                        data['user'] = user
                    else:
                        raise serializers.ValidationError(_('Ce compte utilisateur est désactivé.'))
                else:
                    raise serializers.ValidationError(_('Identifiant ou mot de passe incorrect.'))
            except User.DoesNotExist:
                raise serializers.ValidationError(_('Identifiant ou mot de passe incorrect.'))
        else:
            raise serializers.ValidationError(_('Les champs identifiant et mot de passe sont requis.'))

        return data


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer pour le changement de mot de passe."""

    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    new_password_confirm = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError(_("Les nouveaux mots de passe ne correspondent pas."))
        return data


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        
        # Ajouter les informations utilisateur à la réponse
        data['user'] = {
            'id': user.id,
            'identifiant': user.identifiant,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
        }
        return data
