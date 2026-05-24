from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from apps.accounts.models import GrupoPolla, PerfilUsuario


def clasificacion_global(request):
    perfiles = (
        PerfilUsuario.objects.select_related("usuario")
        .order_by("-puntos_totales")[:100]
    )
    mi_posicion = None
    if request.user.is_authenticated:
        mejor_que_yo = PerfilUsuario.objects.filter(
            puntos_totales__gt=request.user.perfil.puntos_totales
        ).count()
        mi_posicion = mejor_que_yo + 1

    return render(request, "leaderboard/clasificacion.html", {
        "perfiles": perfiles,
        "mi_posicion": mi_posicion,
    })


@login_required
def clasificacion_grupo(request, pk):
    grupo = get_object_or_404(GrupoPolla, pk=pk)
    if not grupo.miembros.filter(pk=request.user.pk).exists() and not grupo.es_publico:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    ranking = grupo.ranking_interno()
    return render(request, "leaderboard/clasificacion_grupo.html", {
        "grupo": grupo,
        "ranking": ranking,
    })
