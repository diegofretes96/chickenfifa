"""
Modelos del torneo: Team, Group, Match.

FIFA 2026 — Formato 48 equipos:
  - 12 grupos de 4 equipos (A–L)
  - Top 2 de cada grupo + 8 mejores terceros → Dieciseisavos (32 equipos, 16 partidos)
  - Octavos → Cuartos → Semifinales → Tercer Puesto → Final
  - Total: 104 partidos
"""
from __future__ import annotations

import logging
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Choices
# ---------------------------------------------------------------------------

class Confederacion(models.TextChoices):
    UEFA = "UEFA", "UEFA (Europa)"
    CONMEBOL = "CONMEBOL", "CONMEBOL (Sudamérica)"
    CONCACAF = "CONCACAF", "CONCACAF (América del Norte/Centro/Caribe)"
    CAF = "CAF", "CAF (África)"
    AFC = "AFC", "AFC (Asia)"
    OFC = "OFC", "OFC (Oceanía)"


class GrupoNombre(models.TextChoices):
    A = "A", "Grupo A"
    B = "B", "Grupo B"
    C = "C", "Grupo C"
    D = "D", "Grupo D"
    E = "E", "Grupo E"
    F = "F", "Grupo F"
    G = "G", "Grupo G"
    H = "H", "Grupo H"
    I = "I", "Grupo I"
    J = "J", "Grupo J"
    K = "K", "Grupo K"
    L = "L", "Grupo L"


class Fase(models.TextChoices):
    GRUPO = "grupo", _("Fase de Grupos")
    DIECISEISAVOS = "dieciseisavos", _("Dieciseisavos de Final")
    OCTAVOS = "octavos", _("Octavos de Final")
    CUARTOS = "cuartos", _("Cuartos de Final")
    SEMIFINAL = "semifinal", _("Semifinal")
    TERCERO = "tercero", _("Tercer Puesto")
    FINAL = "final", _("Final")


# ---------------------------------------------------------------------------
# Team
# ---------------------------------------------------------------------------

class Equipo(models.Model):
    """Selección nacional participante en el Mundial 2026."""

    nombre = models.CharField(_("nombre"), max_length=100)
    codigo_fifa = models.CharField(
        _("código FIFA"),
        max_length=3,
        unique=True,
        help_text=_("Código ISO de 3 letras. Ej: ARG, BRA, ESP"),
    )
    grupo = models.CharField(
        _("grupo"),
        max_length=1,
        choices=GrupoNombre.choices,
        db_index=True,
    )
    confederacion = models.CharField(
        _("confederación"),
        max_length=20,
        choices=Confederacion.choices,
    )
    bandera = models.ImageField(
        _("bandera"),
        upload_to="banderas/",
        blank=True,
        null=True,
    )

    # Resultados de la fase de grupos (calculados automáticamente)
    partidos_jugados = models.PositiveSmallIntegerField(_("PJ"), default=0)
    victorias = models.PositiveSmallIntegerField(_("G"), default=0)
    empates = models.PositiveSmallIntegerField(_("E"), default=0)
    derrotas = models.PositiveSmallIntegerField(_("P"), default=0)
    goles_favor = models.PositiveSmallIntegerField(_("GF"), default=0)
    goles_contra = models.PositiveSmallIntegerField(_("GC"), default=0)
    puntos_grupo = models.PositiveSmallIntegerField(_("Pts"), default=0)
    posicion_grupo = models.PositiveSmallIntegerField(
        _("posición en grupo"),
        default=0,
        help_text=_("1=primero, 2=segundo, 3=tercero, 4=cuarto"),
    )
    clasifico = models.BooleanField(
        _("clasificó a fase eliminatoria"),
        default=False,
    )

    class Meta:
        verbose_name = _("equipo")
        verbose_name_plural = _("equipos")
        ordering = ["grupo", "posicion_grupo", "nombre"]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.codigo_fifa})"

    @property
    def diferencia_goles(self) -> int:
        return self.goles_favor - self.goles_contra

    def actualizar_estadisticas_grupo(self) -> None:
        """Recalcula victorias/empates/derrotas/goles desde los partidos jugados."""
        from apps.tournament.models import Partido  # evita circular import

        self.partidos_jugados = 0
        self.victorias = 0
        self.empates = 0
        self.derrotas = 0
        self.goles_favor = 0
        self.goles_contra = 0
        self.puntos_grupo = 0

        partidos = Partido.objects.filter(
            fase=Fase.GRUPO,
            finalizado=True,
        ).filter(
            models.Q(equipo_local=self) | models.Q(equipo_visitante=self)
        )

        for partido in partidos:
            self.partidos_jugados += 1
            if partido.equipo_local == self:
                gf, gc = partido.goles_local, partido.goles_visitante
            else:
                gf, gc = partido.goles_visitante, partido.goles_local

            self.goles_favor += gf
            self.goles_contra += gc

            if gf > gc:
                self.victorias += 1
                self.puntos_grupo += 3
            elif gf == gc:
                self.empates += 1
                self.puntos_grupo += 1
            else:
                self.derrotas += 1

        self.save(update_fields=[
            "partidos_jugados", "victorias", "empates", "derrotas",
            "goles_favor", "goles_contra", "puntos_grupo",
        ])


# ---------------------------------------------------------------------------
# Match
# ---------------------------------------------------------------------------

class Partido(models.Model):
    """
    Partido del torneo.

    Para la fase de grupos: equipo_local y equipo_visitante son fijos.
    Para fases eliminatorias: pueden ser NULL hasta que se determinen
    los clasificados; se usan los campos de origen para rastrear qué
    partido/posición alimenta este slot.
    """

    numero_partido = models.PositiveSmallIntegerField(
        _("N° de partido"),
        unique=True,
        help_text=_("Numeración oficial FIFA (1–104)"),
    )
    fase = models.CharField(
        _("fase"),
        max_length=20,
        choices=Fase.choices,
        db_index=True,
    )
    grupo = models.CharField(
        _("grupo"),
        max_length=1,
        choices=GrupoNombre.choices,
        blank=True,
        null=True,
        help_text=_("Solo para partidos de fase de grupos"),
    )

    # Equipos — pueden ser NULL en fase eliminatoria hasta que se conozcan
    equipo_local = models.ForeignKey(
        Equipo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="partidos_local",
        verbose_name=_("equipo local"),
    )
    equipo_visitante = models.ForeignKey(
        Equipo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="partidos_visitante",
        verbose_name=_("equipo visitante"),
    )

    # Placeholder textual para fases eliminatorias antes de conocerse los equipos
    placeholder_local = models.CharField(
        _("placeholder local"),
        max_length=60,
        blank=True,
        help_text=_("Ej: 'Ganador Partido 37' o '1° Grupo A'"),
    )
    placeholder_visitante = models.CharField(
        _("placeholder visitante"),
        max_length=60,
        blank=True,
    )

    # Resultado oficial
    goles_local = models.PositiveSmallIntegerField(_("goles local"), null=True, blank=True)
    goles_visitante = models.PositiveSmallIntegerField(_("goles visitante"), null=True, blank=True)

    # Desempate en eliminatorias (no cuenta para pronósticos de score)
    penales_local = models.PositiveSmallIntegerField(_("penales local"), null=True, blank=True)
    penales_visitante = models.PositiveSmallIntegerField(_("penales visitante"), null=True, blank=True)

    # Calendario
    fecha_hora = models.DateTimeField(_("fecha y hora (UTC)"), db_index=True)
    sede = models.CharField(_("sede"), max_length=100, blank=True)
    ciudad = models.CharField(_("ciudad"), max_length=80, blank=True)

    # Estado
    finalizado = models.BooleanField(_("finalizado"), default=False, db_index=True)

    class Meta:
        verbose_name = _("partido")
        verbose_name_plural = _("partidos")
        ordering = ["fecha_hora", "numero_partido"]
        indexes = [
            models.Index(fields=["fase", "finalizado"], name="tournament__fase_fec_idx"),
            models.Index(fields=["fase", "grupo"], name="tournament__fase_grp_idx"),
        ]

    def __str__(self) -> str:
        local = self.equipo_local or self.placeholder_local or "TBD"
        visitante = self.equipo_visitante or self.placeholder_visitante or "TBD"
        return f"[{self.numero_partido}] {local} vs {visitante} ({self.get_fase_display()})"

    # ------------------------------------------------------------------
    # Deadline logic
    # ------------------------------------------------------------------

    @property
    def fecha_cierre_pronostico(self) -> timezone.datetime:
        """Momento exacto en que se bloquean los pronósticos para este partido."""
        lock_minutes = getattr(settings, "PREDICTION_LOCK_MINUTES", 30)
        return self.fecha_hora - timedelta(minutes=lock_minutes)

    @property
    def pronosticos_cerrados(self) -> bool:
        return timezone.now() >= self.fecha_cierre_pronostico

    # ------------------------------------------------------------------
    # Result helpers
    # ------------------------------------------------------------------

    @property
    def resultado_disponible(self) -> bool:
        return self.goles_local is not None and self.goles_visitante is not None

    @property
    def ganador(self) -> Equipo | None:
        """Devuelve el equipo ganador. None en caso de empate o sin resultado."""
        if not self.resultado_disponible:
            return None
        if self.goles_local > self.goles_visitante:
            return self.equipo_local
        if self.goles_visitante > self.goles_local:
            return self.equipo_visitante
        # En eliminatorias, desempate por penales
        if self.penales_local is not None and self.penales_visitante is not None:
            return self.equipo_local if self.penales_local > self.penales_visitante else self.equipo_visitante
        return None  # empate en grupos

    @property
    def es_empate(self) -> bool:
        return (
            self.resultado_disponible
            and self.goles_local == self.goles_visitante
            and self.penales_local is None
        )

    def nombre_local_display(self) -> str:
        if self.equipo_local:
            return self.equipo_local.nombre
        return self.placeholder_local or "Por determinar"

    def nombre_visitante_display(self) -> str:
        if self.equipo_visitante:
            return self.equipo_visitante.nombre
        return self.placeholder_visitante or "Por determinar"
