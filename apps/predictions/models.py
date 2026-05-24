"""
Modelos de pronósticos.

Pronostico: predicción de resultado (score) para cada partido.
PronosticoClasificacion: predicción de qué equipo avanza en fase eliminatoria.

Sistema de puntos:
  - Resultado exacto (score exacto):         5 pts
  - Resultado correcto (W/D/L, score errado): 3 pts
  - Equipo clasificado a siguiente fase:      2 pts (solo fase eliminatoria)
"""
from __future__ import annotations

import logging

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.tournament.models import Equipo, Fase, Partido

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes de puntuación
# ---------------------------------------------------------------------------
PUNTOS_EXACTO = 5
PUNTOS_RESULTADO = 3
PUNTOS_CLASIFICADO = 2


# ---------------------------------------------------------------------------
# Pronostico (predicción de score)
# ---------------------------------------------------------------------------

class Pronostico(models.Model):
    """
    Pronóstico de score que un usuario hace para un partido.

    Reglas:
      - Solo se puede crear/modificar antes del cierre (fecha_cierre_pronostico).
      - Un usuario solo puede tener un pronóstico por partido (unique_together).
      - Los puntos se calculan asincrónicamente cuando el partido finaliza.
    """

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="pronosticos",
        verbose_name=_("usuario"),
    )
    partido = models.ForeignKey(
        Partido,
        on_delete=models.CASCADE,
        related_name="pronosticos",
        verbose_name=_("partido"),
    )

    # Predicción del usuario
    goles_local = models.PositiveSmallIntegerField(_("goles local pronosticados"))
    goles_visitante = models.PositiveSmallIntegerField(_("goles visitante pronosticados"))

    # Resultado del cálculo (NULL hasta que el partido finalice)
    puntos_otorgados = models.PositiveSmallIntegerField(
        _("puntos otorgados"),
        null=True,
        blank=True,
        help_text=_("Se calcula automáticamente al registrar el resultado oficial"),
    )
    detalle_puntos = models.JSONField(
        _("detalle de puntos"),
        null=True,
        blank=True,
        help_text=_("Desglose del cálculo: {'exacto': bool, 'resultado': bool, 'puntos': int}"),
    )

    # Timestamps
    creado_en = models.DateTimeField(_("creado en"), auto_now_add=True)
    actualizado_en = models.DateTimeField(_("actualizado en"), auto_now=True)

    class Meta:
        verbose_name = _("pronóstico")
        verbose_name_plural = _("pronósticos")
        unique_together = [("usuario", "partido")]
        ordering = ["partido__fecha_hora"]
        indexes = [
            models.Index(fields=["usuario", "partido"], name="predictions__user_partido_idx"),
            models.Index(fields=["partido", "puntos_otorgados"], name="predictions__partido_pts_idx"),
        ]

    def __str__(self) -> str:
        return (
            f"{self.usuario.username}: "
            f"{self.partido.nombre_local_display()} {self.goles_local}–"
            f"{self.goles_visitante} {self.partido.nombre_visitante_display()}"
        )

    # ------------------------------------------------------------------
    # Validaciones
    # ------------------------------------------------------------------

    def clean(self) -> None:
        if self.partido.pronosticos_cerrados:
            raise ValidationError(
                _("No se pueden enviar pronósticos: el partido ya comenzó o está por comenzar.")
            )
        if self.partido.finalizado:
            raise ValidationError(_("El partido ya finalizó."))

    def save(self, *args, **kwargs):
        # Ejecutar clean() solo en creación/actualización de usuario (no en recálculo admin)
        if not kwargs.pop("skip_validation", False):
            self.clean()
        super().save(*args, **kwargs)

    # ------------------------------------------------------------------
    # Cálculo de puntos
    # ------------------------------------------------------------------

    def calcular_puntos(self) -> int:
        """
        Calcula y persiste los puntos para este pronóstico.
        Retorna los puntos otorgados.
        Debe llamarse solo cuando partido.finalizado == True.
        """
        if not self.partido.resultado_disponible:
            logger.warning("Intento de calcular puntos sin resultado: partido %s", self.partido.pk)
            return 0

        goles_local_real = self.partido.goles_local
        goles_visitante_real = self.partido.goles_visitante

        es_exacto = (
            self.goles_local == goles_local_real
            and self.goles_visitante == goles_visitante_real
        )

        resultado_correcto = (
            _obtener_resultado(self.goles_local, self.goles_visitante)
            == _obtener_resultado(goles_local_real, goles_visitante_real)
        )

        if es_exacto:
            puntos = PUNTOS_EXACTO
        elif resultado_correcto:
            puntos = PUNTOS_RESULTADO
        else:
            puntos = 0

        self.puntos_otorgados = puntos
        self.detalle_puntos = {
            "exacto": es_exacto,
            "resultado_correcto": resultado_correcto and not es_exacto,
            "puntos": puntos,
            "resultado_real": f"{goles_local_real}–{goles_visitante_real}",
            "pronostico": f"{self.goles_local}–{self.goles_visitante}",
        }
        self.save(skip_validation=True, update_fields=["puntos_otorgados", "detalle_puntos"])
        return puntos


def _obtener_resultado(goles_local: int, goles_visitante: int) -> str:
    """Retorna 'L' (local), 'V' (visitante) o 'E' (empate)."""
    if goles_local > goles_visitante:
        return "L"
    if goles_visitante > goles_local:
        return "V"
    return "E"


# ---------------------------------------------------------------------------
# PronosticoClasificacion (pronóstico de avance en eliminatorias)
# ---------------------------------------------------------------------------

class PronosticoClasificacion(models.Model):
    """
    Predicción del usuario sobre qué equipo avanza en un partido eliminatorio.

    Se crea automáticamente cuando se define el bracket eliminatorio.
    Otorga PUNTOS_CLASIFICADO si el equipo elegido avanza efectivamente.

    Nota: no se pronostica el score de eliminatorias aquí; eso lo hace Pronostico.
    Este modelo es exclusivo para el bono de "quién clasifica".
    """

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="pronosticos_clasificacion",
        verbose_name=_("usuario"),
    )
    partido = models.ForeignKey(
        Partido,
        on_delete=models.CASCADE,
        related_name="pronosticos_clasificacion",
        verbose_name=_("partido eliminatorio"),
    )
    equipo_elegido = models.ForeignKey(
        Equipo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pronosticos_como_clasificado",
        verbose_name=_("equipo elegido para clasificar"),
    )

    puntos_otorgados = models.PositiveSmallIntegerField(
        _("puntos otorgados"),
        null=True,
        blank=True,
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("pronóstico de clasificación")
        verbose_name_plural = _("pronósticos de clasificación")
        unique_together = [("usuario", "partido")]
        ordering = ["partido__fecha_hora"]

    def __str__(self) -> str:
        equipo = self.equipo_elegido or "Sin elegir"
        return f"{self.usuario.username} → {equipo} clasifica ({self.partido})"

    def clean(self) -> None:
        if self.partido.fase == Fase.GRUPO:
            raise ValidationError(
                _("Los pronósticos de clasificación solo aplican a fases eliminatorias.")
            )
        if self.equipo_elegido and self.equipo_elegido not in (
            self.partido.equipo_local,
            self.partido.equipo_visitante,
        ):
            raise ValidationError(
                _("El equipo elegido debe ser uno de los participantes del partido.")
            )
        if self.partido.pronosticos_cerrados:
            raise ValidationError(
                _("El plazo para pronosticar este partido ya cerró.")
            )

    def calcular_puntos(self) -> int:
        """
        Otorga PUNTOS_CLASIFICADO si el equipo elegido es el ganador del partido.
        """
        if not self.partido.resultado_disponible:
            return 0

        ganador = self.partido.ganador
        acierto = ganador is not None and ganador == self.equipo_elegido
        puntos = PUNTOS_CLASIFICADO if acierto else 0
        self.puntos_otorgados = puntos
        self.save(update_fields=["puntos_otorgados"])
        return puntos
