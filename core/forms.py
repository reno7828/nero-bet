from django import forms
from django.contrib.auth.models import User

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Mot de passe'}))
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirmer le mot de passe'}))

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': "Nom d'utilisateur"}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email'}),
        }

    # Vérification Pseudo unique
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return username

    # Vérification Email unique
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cet email est déjà lié à un compte.")
        return email

    # Vérification correspondance mots de passe
    def clean_password_confirm(self):
        p1 = self.cleaned_data.get('password')
        p2 = self.cleaned_data.get('password_confirm')
        if p1 != p2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user