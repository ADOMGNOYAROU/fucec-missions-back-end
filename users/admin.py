from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import User, Entite, Service, UserRole

class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = '__all__'

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('identifiant', 'email')

class UserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    list_display = ('identifiant', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('identifiant', 'first_name', 'last_name', 'email')
    ordering = ('identifiant',)
    
    fieldsets = (
        (None, {'fields': ('identifiant', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Additional info'), {
            'fields': (
                'role', 
                'manager', 
                'matricule', 
                'telephone', 
                'signature',
                'entite',
                'agence',
                'service',
                'direction',
            )
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'identifiant', 
                'email', 
                'password1', 
                'password2', 
                'first_name', 
                'last_name', 
                'role',
                'is_staff',
                'is_active'
            ),
        }),
    )

class EntiteAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code', 'type', 'parent', 'responsable')
    list_filter = ('type',)
    search_fields = ('nom', 'code')
    raw_id_fields = ('parent', 'responsable')
    readonly_fields = ('date_creation',)


class ServiceAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'chef', 'budget_annuel', 'actif')
    list_filter = ('actif',)
    search_fields = ('code', 'nom', 'description')
    raw_id_fields = ('chef',)
    readonly_fields = ('date_creation',)
    list_editable = ('actif',)


# Enregistrement des modèles avec leurs configurations personnalisées
admin.site.register(User, UserAdmin)
admin.site.register(Entite, EntiteAdmin)
admin.site.register(Service, ServiceAdmin)
