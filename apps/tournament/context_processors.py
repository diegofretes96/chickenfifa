"""
Context processor que inyecta estado global del torneo en todos los templates.
"""
from django.utils import timezone

from apps.tournament.models import Fase, Partido


def tournament_context(request):
    ahora = timezone.now()

    # Próximo partido no finalizado
    proximo = (
        Partido.objects.filter(finalizado=False, fecha_hora__gte=ahora)
        .select_related("equipo_local", "equipo_visitante")
        .order_by("fecha_hora")
        .first()
    )

    # Fase actual activa
    fases_activas = (
        Partido.objects.filter(finalizado=False)
        .values_list("fase", flat=True)
        .distinct()
    )

    return {
        "proximo_partido": proximo,
        "fases_activas": list(fases_activas),
        "Fase": Fase,
    }
