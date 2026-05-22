"""
Motor de recálculo de puntos.

Llamado desde el admin de Django (via Celery) cada vez que se registra
un resultado oficial. Recalcula todos los pronósticos del partido y
actualiza los totales de cada usuario.
"""
from __future__ import annotations

import logging

from django.db import transaction

from apps.tournament.models import Partido

logger = logging.getLogger(__name__)


@transaction.atomic
def recalcular_puntos_partido(partido_pk: int) -> dict:
    """
    Recalcula puntos para todos los pronósticos de un partido.

    Retorna un resumen: {'partido': id, 'pronosticos': n, 'clasificacion': n}
    """
    from apps.predictions.models import Pronostico, PronosticoClasificacion
    from apps.accounts.models import PerfilUsuario

    partido = Partido.objects.select_related(
        "equipo_local", "equipo_visitante"
    ).get(pk=partido_pk)

    if not partido.finalizado or not partido.resultado_disponible:
        logger.warning("Partido %s no está finalizado aún, omitiendo recálculo.", partido_pk)
        return {"error": "partido_no_finalizado"}

    logger.info("Recalculando puntos para partido %s (%s)", partido_pk, partido)

    # --- Score predictions ---
    pronosticos = Pronostico.objects.filter(partido=partido).select_related("usuario")
    usuarios_afectados: set[int] = set()

    for pron in pronosticos:
        pron.calcular_puntos()
        usuarios_afectados.add(pron.usuario_id)

    # --- Clasificación predictions (solo eliminatorias) ---
    clafs = PronosticoClasificacion.objects.filter(partido=partido).select_related("usuario")
    for clf in clafs:
        clf.calcular_puntos()
        usuarios_afectados.add(clf.usuario_id)

    # --- Actualizar totales de perfil ---
    perfiles = PerfilUsuario.objects.filter(usuario_id__in=usuarios_afectados)
    for perfil in perfiles:
        perfil.recalcular_puntos()

    logger.info(
        "Recálculo completo: %d pronósticos, %d clasificación, %d usuarios",
        pronosticos.count(), clafs.count(), len(usuarios_afectados),
    )

    return {
        "partido": partido_pk,
        "pronosticos": pronosticos.count(),
        "clasificacion": clafs.count(),
        "usuarios_actualizados": len(usuarios_afectados),
    }
