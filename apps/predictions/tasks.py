"""
Tareas Celery para el recálculo asíncrono de puntos.
Se disparan desde el admin al guardar un resultado oficial.
"""
from celery import shared_task

from apps.predictions.scoring import recalcular_puntos_partido


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def tarea_recalcular_puntos(self, partido_pk: int) -> dict:
    """
    Tarea asíncrona: recalcula puntos de todos los pronósticos de un partido
    y actualiza el total de cada usuario afectado.
    """
    try:
        return recalcular_puntos_partido(partido_pk)
    except Exception as exc:
        raise self.retry(exc=exc)
