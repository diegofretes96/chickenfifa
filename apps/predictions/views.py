from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.predictions.models import Pronostico, PronosticoClasificacion
from apps.tournament.models import Fase, Partido


@login_required
def mis_pronosticos(request):
    pronosticos = (
        Pronostico.objects.filter(usuario=request.user)
        .select_related("partido__equipo_local", "partido__equipo_visitante")
        .order_by("partido__fecha_hora")
    )
    return render(request, "predictions/mis_pronosticos.html", {"pronosticos": pronosticos})


@login_required
def pronosticos_grupo(request):
    partidos = (
        Partido.objects.filter(fase=Fase.GRUPO)
        .select_related("equipo_local", "equipo_visitante")
        .order_by("grupo", "fecha_hora")
    )
    pronosticos_usuario = {
        p.partido_id: p
        for p in Pronostico.objects.filter(usuario=request.user, partido__fase=Fase.GRUPO)
    }
    return render(request, "predictions/grupo.html", {
        "partidos": partidos,
        "pronosticos_usuario": pronosticos_usuario,
    })


@login_required
def guardar_pronostico(request, partido_pk):
    partido = get_object_or_404(Partido, pk=partido_pk)

    if partido.pronosticos_cerrados:
        messages.error(request, "El plazo para pronosticar este partido ya cerró.")
        return redirect("predictions:grupo")

    if request.method == "POST":
        try:
            goles_local = int(request.POST.get("goles_local", -1))
            goles_visitante = int(request.POST.get("goles_visitante", -1))
            if goles_local < 0 or goles_visitante < 0:
                raise ValueError("Valores inválidos")
        except (ValueError, TypeError):
            messages.error(request, "Ingresa valores válidos (0 o más goles).")
            return redirect(request.META.get("HTTP_REFERER", "predictions:grupo"))

        pronostico, creado = Pronostico.objects.update_or_create(
            usuario=request.user,
            partido=partido,
            defaults={
                "goles_local": goles_local,
                "goles_visitante": goles_visitante,
            },
        )
        pronostico.save(skip_validation=True)
        accion = "guardado" if creado else "actualizado"
        messages.success(request, f"Pronóstico {accion}: {goles_local}–{goles_visitante}")

    next_url = request.POST.get("next") or "predictions:grupo"
    return redirect(next_url)


@login_required
def pronosticos_eliminatoria(request):
    fases = [Fase.DIECISEISAVOS, Fase.OCTAVOS, Fase.CUARTOS, Fase.SEMIFINAL, Fase.TERCERO, Fase.FINAL]
    partidos = (
        Partido.objects.filter(fase__in=fases)
        .select_related("equipo_local", "equipo_visitante")
        .order_by("numero_partido")
    )
    pronosticos_score = {
        p.partido_id: p
        for p in Pronostico.objects.filter(usuario=request.user, partido__fase__in=fases)
    }
    pronosticos_clf = {
        p.partido_id: p
        for p in PronosticoClasificacion.objects.filter(
            usuario=request.user, partido__fase__in=fases
        ).select_related("equipo_elegido")
    }
    return render(request, "predictions/eliminatoria.html", {
        "partidos": partidos,
        "pronosticos_score": pronosticos_score,
        "pronosticos_clf": pronosticos_clf,
        "Fase": Fase,
    })
