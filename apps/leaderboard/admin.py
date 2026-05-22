from django.contrib import admin

from apps.leaderboard.models import SnapshotClasificacion


@admin.register(SnapshotClasificacion)
class SnapshotClasificacionAdmin(admin.ModelAdmin):
    list_display = ["posicion", "usuario", "puntos", "tendencia", "fecha"]
    list_filter = ["fecha"]
    search_fields = ["usuario__username"]
    readonly_fields = ["fecha", "generado_en"]
    ordering = ["fecha", "posicion"]
