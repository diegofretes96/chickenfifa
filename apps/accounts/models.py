"""
Modelos de usuario: PerfilUsuario y GrupoPolla (grupos privados de quiniela).
"""
import secrets
import string

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _


def _generar_codigo_invitacion() -> str:
    """Genera un código de invitación de 8 caracteres alfanumérico en mayúsculas."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(8))


# ---------------------------------------------------------------------------
# PerfilUsuario
# ---------------------------------------------------------------------------

class PerfilUsuario(models.Model):
    """
    Extensión del modelo User de Django.
    Almacena puntos totales y preferencias del usuario.
    """

    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="perfil",
        verbose_name=_("usuario"),
    )
    nombre_display = models.CharField(
        _("nombre a mostrar"),
        max_length=50,
        blank=True,
        help_text=_("Alias público en la tabla de clasificación"),
    )
    avatar = models.ImageField(
        _("avatar"),
        upload_to="avatares/",
        blank=True,
        null=True,
    )
    puntos_totales = models.IntegerField(
        _("puntos totales"),
        default=0,
        db_index=True,
    )
    fecha_registro = models.DateTimeField(_("fecha de registro"), auto_now_add=True)
    bio = models.CharField(_("bio"), max_length=200, blank=True)

    class Meta:
        verbose_name = _("perfil de usuario")
        verbose_name_plural = _("perfiles de usuario")
        ordering = ["-puntos_totales"]

    def __str__(self) -> str:
        return self.nombre_display or self.usuario.username

    def recalcular_puntos(self) -> None:
        """Suma todos los puntos de pronósticos del usuario y actualiza el campo."""
        from apps.predictions.models import Pronostico

        total = (
            Pronostico.objects.filter(usuario=self.usuario, puntos_otorgados__isnull=False)
            .aggregate(total=models.Sum("puntos_otorgados"))["total"]
            or 0
        )
        self.puntos_totales = total
        self.save(update_fields=["puntos_totales"])


@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(
            usuario=instance,
            nombre_display=instance.username,
        )


@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    if hasattr(instance, "perfil"):
        instance.perfil.save()


# ---------------------------------------------------------------------------
# GrupoPolla (grupos privados de quiniela)
# ---------------------------------------------------------------------------

class GrupoPolla(models.Model):
    """
    Grupo privado de quiniela.
    Los usuarios se unen con un código de invitación único.
    La tabla de clasificación interna solo muestra miembros del grupo.
    """

    nombre = models.CharField(_("nombre del grupo"), max_length=80)
    codigo_invitacion = models.CharField(
        _("código de invitación"),
        max_length=8,
        unique=True,
        default=_generar_codigo_invitacion,
        editable=False,
    )
    creador = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="grupos_creados",
        verbose_name=_("creador"),
    )
    miembros = models.ManyToManyField(
        User,
        related_name="grupos_polla",
        verbose_name=_("miembros"),
        blank=True,
    )
    descripcion = models.TextField(_("descripción"), blank=True)
    fecha_creacion = models.DateTimeField(_("fecha de creación"), auto_now_add=True)
    es_publico = models.BooleanField(
        _("grupo público"),
        default=False,
        help_text=_("Si es público, aparece en el listado de grupos sin necesitar código"),
    )

    class Meta:
        verbose_name = _("grupo polla")
        verbose_name_plural = _("grupos polla")
        ordering = ["nombre"]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.codigo_invitacion})"

    def total_miembros(self) -> int:
        return self.miembros.count()

    def ranking_interno(self):
        """QuerySet de perfiles de usuarios del grupo ordenados por puntos."""
        from apps.accounts.models import PerfilUsuario

        return PerfilUsuario.objects.filter(
            usuario__in=self.miembros.all()
        ).select_related("usuario").order_by("-puntos_totales")
