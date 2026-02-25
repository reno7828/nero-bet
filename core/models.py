import os
from django.db import models
from django.contrib.auth.models import User
from cryptography.fernet import Fernet

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_beta_tester = models.BooleanField(default=False)  # Ajoute cette ligne
    # Les champs réels en base de données sont binaires (cryptés)
    mistral_key_encrypted = models.BinaryField(null=True, blank=True)
    football_key_encrypted = models.BinaryField(null=True, blank=True)

    def _get_fernet(self):
        # Récupère la clé dans ton fichier .env
        key = os.getenv('ENCRYPTION_KEY')
        if not key:
            raise ValueError("ENCRYPTION_KEY manquante dans le fichier .env")
        return Fernet(key.encode())

    # On utilise des @property pour manipuler les clés comme du texte normal
    @property
    def mistral_key(self):
        if not self.mistral_key_encrypted: return ""
        return self._get_fernet().decrypt(self.mistral_key_encrypted).decode()

    @mistral_key.setter
    def mistral_key(self, value):
        if value:
            self.mistral_key_encrypted = self._get_fernet().encrypt(value.encode())

    @property
    def football_key(self):
        if not self.football_key_encrypted: return ""
        return self._get_fernet().decrypt(self.football_key_encrypted).decode()

    @football_key.setter
    def football_key(self, value):
        if value:
            self.football_key_encrypted = self._get_fernet().encrypt(value.encode())

    def __str__(self):
        return f"Profil de {self.user.username}"