"""
Admin del torneo: gestión de equipos y partidos con trigger automático
de recálculo de puntos al guardar resultados.
"""
from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _

from apps.tournament.models import Equipo, Partido


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ["nombre", "codigo_fifa", "grupo", "confederacion", "clasifico"]
    list_filter = ["grupo", "confederacion", "clasifico"]
    search_fields = ["nombre", "codigo_fifa"]
    list_editable = ["clasifico"]
    ordering = ["grupo", "posicion_grupo"]

    fieldsets = (
        (None, {"fields": ("nombre", "codigo_fifa", "confederacion", "grupo", "bandera")}),
        (
            _("Estadísticas de grupo"),
            {
                "fields": (
                    "partidos_jugados", "victorias", "empates", "derrotas",
                    "goles_favor", "goles_contra", "puntos_grupo",
                    "posicion_grupo", "clasifico",
                ),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(Partido)
class PartidoAdmin(admin.ModelAdmin):
    list_display = [
        "numero_partido", "fase", "grupo",
        "equipo_local", "goles_local",
        "equipo_visitante", "goles_visitante",
        "fecha_hora", "finalizado",
    ]
    list_filter = ["fase", "grupo", "finalizado"]
    search_fields = ["equipo_local__nombre", "equipo_visitante__nombre", "numero_partido"]
    list_editable = ["goles_local", "goles_visitante", "finalizado"]
    date_hierarchy = "fecha_hora"
    ordering = ["fecha_hora"]

    fieldsets = (
        (
            _("Identificación"),
            {"fields": ("numero_partido", "fase", "grupo", "fecha_hora", "sede", "ciudad")},
        ),
        (
            _("Equipos"),
            {
                "fields": (
                    ("equipo_local", "placeholder_local"),
                    ("equipo_visitante", "placeholder_visitante"),
                )
            },
        ),
        (
            _("Resultado oficial"),
            {
                "fields": (
                    ("goles_local", "goles_visitante"),
                    ("penales_local", "penales_visitante"),
                    "finalizado",
                )
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        """
        Tras guardar, si el partido fue marcado como finalizado con resultado,
        dispara la tarea Celery de recálculo de puntos.
        """
        resultado_previo_finalizado = change and form.initial.get("finalizado", False)
        super().save_model(request, obj, form, change)

        if obj.finalizado and obj.resultado_disponible and not resultado_previo_finalizado:
            from apps.predictions.tasks import tarea_recalcular_puntos

            tarea_recalcular_puntos.delay(obj.pk)
            self.message_user(
                request,
                _(
                    f"Resultado registrado. Recálculo de puntos para el partido "
                    f"#{obj.numero_partido} en proceso..."
                ),
                messages.SUCCESS,
            )

            # Actualizar estadísticas de grupo si es fase de grupos
            if obj.fase == "grupo":
                for equipo in filter(None, [obj.equipo_local, obj.equipo_visitante]):
                    equipo.actualizar_estadisticas_grupo()
