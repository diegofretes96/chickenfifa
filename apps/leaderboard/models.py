"""
Snapshot diario de la tabla de clasificación para performance.

En lugar de calcular el ranking en tiempo real (JOIN costoso con N usuarios),
guardamos un snapshot actualizado cada vez que se recalculan puntos.
La tabla en vivo sigue siendo la tabla de PerfilUsuario, pero este modelo
permite mostrar posición anterior y tendencia (subió/bajó/igual).
"""
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _


class SnapshotClasificacion(models.Model):
    """
    Posición del usuario en la clasificación global en un momento dado.
    Se regenera tras cada recálculo de puntos.
    """

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="snapshots_clasificacion",
        verbose_name=_("usuario"),
    )
    posicion = models.PositiveIntegerField(_("posición"))
    posicion_anterior = models.PositiveIntegerField(_("posición anterior"), null=True, blank=True)
    puntos = models.IntegerField(_("puntos"))
    puntos_exactos = models.PositiveIntegerField(_("pronósticos exactos"), default=0)
    puntos_resultado = models.PositiveIntegerField(_("pronósticos resultado correcto"), default=0)
    fecha = models.DateField(_("fecha"), auto_now_add=True, db_index=True)
    generado_en = models.DateTimeField(_("generado en"), auto_now=True)

    class Meta:
        verbose_name = _("snapshot de clasificación")
        verbose_name_plural = _("snapshots de clasificación")
        unique_together = [("usuario", "fecha")]
        ordering = ["posicion"]
        get_latest_by = "generado_en"

    def __str__(self) -> str:
        return f"#{self.posicion} {self.usuario.username} — {self.puntos} pts ({self.fecha})"

    @property
    def tendencia(self) -> str:
        """Retorna '↑', '↓' o '=' comparando con posición anterior."""
        if self.posicion_anterior is None:
            return "nuevo"
        if self.posicion < self.posicion_anterior:
            return "↑"
        if self.posicion > self.posicion_anterior:
            return "↓"
        return "="
