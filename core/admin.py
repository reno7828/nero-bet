from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    # On cache les champs cryptés, mais on laisse le champ Beta visible
    exclude = ('mistral_key_encrypted', 'football_key_encrypted')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    # Ajout de is_beta_tester dans la vue en liste
    list_display = ('user', 'is_beta_tester', 'has_mistral_key', 'has_football_key')

    # PERMET DE COCHER "BETA" DIRECTEMENT DANS LA LISTE (Gain de temps !)
    list_editable = ('is_beta_tester',)

    exclude = ('mistral_key_encrypted', 'football_key_encrypted')

    def has_mistral_key(self, obj):
        return bool(obj.mistral_key_encrypted)

    has_mistral_key.boolean = True
    has_mistral_key.short_description = "Clé Mistral"

    def has_football_key(self, obj):
        return bool(obj.football_key_encrypted)

    has_football_key.boolean = True
    has_football_key.short_description = "Clé Football"


# Intégration du profil dans la page Utilisateur standard
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    # On ajoute aussi la colonne Beta dans la liste des utilisateurs pour plus de clarté
    list_display = BaseUserAdmin.list_display + ('get_beta_status',)

    def get_beta_status(self, obj):
        return obj.profile.is_beta_tester

    get_beta_status.boolean = True
    get_beta_status.short_description = "Bêta-testeur"


admin.site.unregister(User)
admin.site.register(User, UserAdmin)