from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from apps.accounts.models import GrupoPolla, PerfilUsuario


class RegistroForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Correo electrónico")

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
        labels = {
            "username": "Nombre de usuario",
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class PerfilForm(forms.ModelForm):
    class Meta:
        model = PerfilUsuario
        fields = ["nombre_display", "bio", "avatar"]
        labels = {
            "nombre_display": "Nombre a mostrar",
            "bio": "Bio",
            "avatar": "Avatar",
        }


class UnirseGrupoForm(forms.Form):
    codigo = forms.CharField(
        max_length=8,
        label="Código de invitación",
        widget=forms.TextInput(attrs={"placeholder": "XXXXXXXX", "class": "form-control text-uppercase"}),
    )

    def clean_codigo(self):
        codigo = self.cleaned_data["codigo"].upper()
        try:
            return GrupoPolla.objects.get(codigo_invitacion=codigo)
        except GrupoPolla.DoesNotExist:
            raise forms.ValidationError("Código inválido. Verifica e intenta de nuevo.")


class CrearGrupoForm(forms.ModelForm):
    class Meta:
        model = GrupoPolla
        fields = ["nombre", "descripcion", "es_publico"]
        labels = {
            "nombre": "Nombre del grupo",
            "descripcion": "Descripción (opcional)",
            "es_publico": "Grupo público",
        }
