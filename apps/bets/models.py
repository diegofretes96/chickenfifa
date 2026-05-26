from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Apuesta(models.Model):
    titulo = models.CharField(max_length=200, verbose_name="Título")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    opcion_a = models.CharField(max_length=150, verbose_name="Opción A")
    opcion_b = models.CharField(max_length=150, verbose_name="Opción B")
    fecha_limite = models.DateTimeField(verbose_name="Fecha límite para apostar")
    fecha_resolucion = models.DateTimeField(verbose_name="Fecha de resolución")
    resultado = models.CharField(
        max_length=1,
        choices=[("A", "Opción A"), ("B", "Opción B")],
        null=True,
        blank=True,
        verbose_name="Resultado",
    )
    creado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="apuestas_creadas"
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_limite"]
        verbose_name = "Apuesta"
        verbose_name_plural = "Apuestas"

    def __str__(self):
        return self.titulo

    @property
    def cerrada(self):
        return timezone.now() >= self.fecha_limite

    @property
    def resuelta(self):
        return self.resultado is not None

    @property
    def votos_a(self):
        return self.votos.filter(opcion="A").count()

    @property
    def votos_b(self):
        return self.votos.filter(opcion="B").count()

    @property
    def total_votos(self):
        return self.votos.count()

    def porcentaje_a(self):
        if self.total_votos == 0:
            return 0
        return round(self.votos_a / self.total_votos * 100)

    def porcentaje_b(self):
        if self.total_votos == 0:
            return 0
        return round(self.votos_b / self.total_votos * 100)


class VotoApuesta(models.Model):
    apuesta = models.ForeignKey(Apuesta, on_delete=models.CASCADE, related_name="votos")
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="votos_apuestas")
    opcion = models.CharField(
        max_length=1, choices=[("A", "Opción A"), ("B", "Opción B")]
    )
    fecha_voto = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("apuesta", "usuario")]
        verbose_name = "Voto"
        verbose_name_plural = "Votos"

    def __str__(self):
        return f"{self.usuario} → {self.apuesta} ({self.opcion})"

    @property
    def acerto(self):
        if not self.apuesta.resuelta:
            return None
        return self.opcion == self.apuesta.resultado
