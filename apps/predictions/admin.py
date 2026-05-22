from django.contrib import admin

from apps.predictions.models import Pronostico, PronosticoClasificacion


@admin.register(Pronostico)
class PronosticoAdmin(admin.ModelAdmin):
    list_display = ["usuario", "partido", "goles_local", "goles_visitante", "puntos_otorgados"]
    list_filter = ["partido__fase", "puntos_otorgados"]
    search_fields = ["usuario__username", "partido__equipo_local__nombre"]
    readonly_fields = ["puntos_otorgados", "detalle_puntos", "creado_en", "actualizado_en"]
    raw_id_fields = ["usuario", "partido"]


@admin.register(PronosticoClasificacion)
class PronosticoClasificacionAdmin(admin.ModelAdmin):
    list_display = ["usuario", "partido", "equipo_elegido", "puntos_otorgados"]
    list_filter = ["partido__fase"]
    search_fields = ["usuario__username"]
    readonly_fields = ["puntos_otorgados", "creado_en", "actualizado_en"]
    raw_id_fields = ["usuario", "partido", "equipo_elegido"]
