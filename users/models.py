from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserRole(models.TextChoices):
    AGENT = 'AGENT', _('Agent')
    CHEF_AGENCE = 'CHEF_AGENCE', _('Chef d\'agence')
    RESPONSABLE_COPEC = 'RESPONSABLE_COPEC', _('Responsable COPEC')
    DG = 'DG', _('Directeur Général')
    RH = 'RH', _('Ressources Humaines')
    COMPTABLE = 'COMPTABLE', _('Comptable')
    ADMIN = 'ADMIN', _('Administrateur')
    DIRECTEUR_FINANCES = 'DIRECTEUR_FINANCES', _('Directeur Finances')
    CHAUFFEUR = 'CHAUFFEUR', _('Chauffeur')


class UserManager(BaseUserManager):
    """Custom manager for User model."""

    def _create_user(self, identifiant, email, password, **extra_fields):
        """Create and save a user with the given email and password."""
        if not identifiant:
            raise ValueError('The Identifiant must be set')
        email = self.normalize_email(email)
        user = self.model(identifiant=identifiant, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, identifiant, email=None, password=None, **extra_fields):
        """Create a regular user."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(identifiant, email, password, **extra_fields)

    def create_superuser(self, identifiant, email, password, **extra_fields):
        """Create a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', UserRole.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(identifiant, email, password, **extra_fields)


class User(AbstractUser):
    """Custom User model for FUCEC Missions."""

    # Remove username field and use identifiant instead
    username = None

    # Custom fields
    identifiant = models.CharField(
        _('Identifiant'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[],
        error_messages={
            'unique': _("A user with that identifiant already exists."),
        },
    )

    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.AGENT,
        verbose_name=_('Rôle')
    )

    manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinates',
        verbose_name=_('Manager')
    )

    # Additional fields
    telephone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Téléphone')
    )

    matricule = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Matricule')
    )

    signature = models.FileField(
        upload_to='signatures/',
        blank=True,
        null=True,
        verbose_name=_('Signature')
    )

    entite = models.ForeignKey(
        'Entite',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='membres',
        verbose_name=_('Entité')
    )

    # Champs spécifiques aux rôles
    agence = models.CharField(max_length=100, blank=True, null=True)
    service = models.CharField(max_length=100, blank=True, null=True)
    direction = models.CharField(max_length=100, blank=True, null=True)

    # Override Meta
    class Meta:
        app_label = 'users'
        verbose_name = _('Utilisateur')
        verbose_name_plural = _('Utilisateurs')
        ordering = ['first_name', 'last_name']

    # Use identifiant as USERNAME_FIELD
    USERNAME_FIELD = 'identifiant'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    objects = UserManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.identifiant})"

    @property
    def is_agent(self):
        return self.role == UserRole.AGENT

    @property
    def is_chef_agence(self):
        return self.role == UserRole.CHEF_AGENCE

    @property
    def is_dg(self):
        return self.role == UserRole.DG

    @property
    def is_rh(self):
        return self.role == UserRole.RH

    @property
    def can_validate(self):
        """Check if user can validate missions."""
        return self.role in [
            UserRole.CHEF_AGENCE,
            UserRole.RESPONSABLE_COPEC,
            UserRole.DG,
            UserRole.RH
        ]

    @property
    def can_create_missions(self):
        """Check if user can create missions."""
        return self.role != UserRole.CHAUFFEUR

    def get_subordinates(self):
        """Get all direct subordinates."""
        return User.objects.filter(manager=self)

    def has_role_or_higher(self, required_roles):
        """Check if user has one of the required roles or higher."""
        role_hierarchy = {
            UserRole.AGENT: 1,
            UserRole.CHEF_AGENCE: 2,
            UserRole.RESPONSABLE_COPEC: 3,
            UserRole.RH: 2,
            UserRole.COMPTABLE: 2,
            UserRole.DIRECTEUR_FINANCES: 2,
            UserRole.DG: 4,
            UserRole.ADMIN: 5,
            UserRole.CHAUFFEUR: 1,
        }

        user_level = role_hierarchy.get(self.role, 0)
        return any(role_hierarchy.get(role, 0) <= user_level for role in required_roles)


class Entite(models.Model):
    """Modèle pour les entités/services de l'organisation."""

    nom = models.CharField(
        _('Nom'),
        max_length=200,
        help_text=_('Nom de l\'entité')
    )

    code = models.CharField(
        _('Code'),
        max_length=20,
        unique=True,
        help_text=_('Code unique de l\'entité')
    )

    type = models.CharField(
        _('Type'),
        max_length=50,
        help_text=_('Type d\'entité (Service, Direction, etc.)')
    )

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='enfants',
        verbose_name=_('Entité parente')
    )

    responsable = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='entites_responsable',
        verbose_name=_('Responsable')
    )

    date_creation = models.DateTimeField(
        _('Date de création'),
        auto_now_add=True
    )

    class Meta:
        app_label = 'users'
        verbose_name = _('Entité')
        verbose_name_plural = _('Entités')
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.code})"

    def get_enfants(self):
        """Récupère tous les enfants directs et indirects."""
        enfants = list(self.enfants.all())
        for enfant in list(enfants):
            enfants.extend(enfant.get_enfants())
