from django.contrib import admin

from .models import Apuesta, VotoApuesta


class VotoInline(admin.TabularInline):
    model = VotoApuesta
    extra = 0
    readonly_fields = ["usuario", "opcion", "fecha_voto"]
    can_delete = False


@admin.register(Apuesta)
class ApuestaAdmin(admin.ModelAdmin):
    list_display = ["titulo", "opcion_a", "opcion_b", "fecha_limite", "fecha_resolucion", "resultado", "total_votos"]
    list_filter = ["resultado"]
    search_fields = ["titulo"]
    readonly_fields = ["creado_por", "creado_en"]
    inlines = [VotoInline]

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(VotoApuesta)
class VotoApuestaAdmin(admin.ModelAdmin):
    list_display = ["usuario", "apuesta", "opcion", "fecha_voto"]
    list_filter = ["opcion", "apuesta"]
    search_fields = ["usuario__username"]
