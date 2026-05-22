from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from apps.accounts.models import GrupoPolla, PerfilUsuario


class PerfilInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    verbose_name_plural = "Perfil"
    fk_name = "usuario"


class UserAdmin(BaseUserAdmin):
    inlines = [PerfilInline]
    list_display = ["username", "email", "first_name", "last_name", "is_staff", "get_puntos"]

    def get_puntos(self, obj):
        return obj.perfil.puntos_totales if hasattr(obj, "perfil") else 0

    get_puntos.short_description = "Puntos"
    get_puntos.admin_order_field = "perfil__puntos_totales"


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(GrupoPolla)
class GrupoPollaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "codigo_invitacion", "creador", "total_miembros", "es_publico"]
    list_filter = ["es_publico"]
    search_fields = ["nombre", "codigo_invitacion"]
    readonly_fields = ["codigo_invitacion", "fecha_creacion"]
    filter_horizontal = ["miembros"]
