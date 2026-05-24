from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from apps.tournament.models import Equipo, Fase, GrupoNombre, Partido


def inicio(request):
    partidos_proximos = (
        Partido.objects.filter(finalizado=False)
        .select_related("equipo_local", "equipo_visitante")
        .order_by("fecha_hora")[:5]
    )
    partidos_recientes = (
        Partido.objects.filter(finalizado=True, goles_local__isnull=False)
        .select_related("equipo_local", "equipo_visitante")
        .order_by("-fecha_hora")[:5]
    )
    return render(request, "tournament/inicio.html", {
        "partidos_proximos": partidos_proximos,
        "partidos_recientes": partidos_recientes,
    })


def grupos(request):
    grupos_data = []
    for letra in GrupoNombre.values:
        equipos = Equipo.objects.filter(grupo=letra).order_by(
            "-puntos_grupo", "-diferencia_goles", "-goles_favor", "nombre"
        )
        partidos = Partido.objects.filter(
            fase=Fase.GRUPO, grupo=letra
        ).select_related("equipo_local", "equipo_visitante").order_by("fecha_hora")
        grupos_data.append({"letra": letra, "equipos": equipos, "partidos": partidos})

    return render(request, "tournament/grupos.html", {"grupos_data": grupos_data})


def bracket(request):
    fases = [
        Fase.DIECISEISAVOS, Fase.OCTAVOS, Fase.CUARTOS,
        Fase.SEMIFINAL, Fase.TERCERO, Fase.FINAL,
    ]
    bracket_data = {}
    for fase in fases:
        bracket_data[fase] = Partido.objects.filter(fase=fase).select_related(
            "equipo_local", "equipo_visitante"
        ).order_by("numero_partido")

    return render(request, "tournament/bracket.html", {
        "bracket_data": bracket_data,
        "Fase": Fase,
    })


def detalle_partido(request, pk):
    partido = get_object_or_404(
        Partido.objects.select_related("equipo_local", "equipo_visitante"), pk=pk
    )
    pronostico = None
    if request.user.is_authenticated:
        from apps.predictions.models import Pronostico
        pronostico = Pronostico.objects.filter(
            usuario=request.user, partido=partido
        ).first()

    return render(request, "tournament/detalle_partido.html", {
        "partido": partido,
        "pronostico": pronostico,
    })
