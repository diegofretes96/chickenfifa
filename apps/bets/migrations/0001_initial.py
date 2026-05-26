import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Apuesta",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("titulo", models.CharField(max_length=200, verbose_name="Título")),
                ("descripcion", models.TextField(blank=True, verbose_name="Descripción")),
                ("opcion_a", models.CharField(max_length=150, verbose_name="Opción A")),
                ("opcion_b", models.CharField(max_length=150, verbose_name="Opción B")),
                ("fecha_limite", models.DateTimeField(verbose_name="Fecha límite para apostar")),
                ("fecha_resolucion", models.DateTimeField(verbose_name="Fecha de resolución")),
                (
                    "resultado",
                    models.CharField(
                        blank=True,
                        choices=[("A", "Opción A"), ("B", "Opción B")],
                        max_length=1,
                        null=True,
                        verbose_name="Resultado",
                    ),
                ),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                (
                    "creado_por",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="apuestas_creadas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Apuesta",
                "verbose_name_plural": "Apuestas",
                "ordering": ["-fecha_limite"],
            },
        ),
        migrations.CreateModel(
            name="VotoApuesta",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "opcion",
                    models.CharField(
                        choices=[("A", "Opción A"), ("B", "Opción B")],
                        max_length=1,
                    ),
                ),
                ("fecha_voto", models.DateTimeField(auto_now_add=True)),
                (
                    "apuesta",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="votos",
                        to="bets.apuesta",
                    ),
                ),
                (
                    "usuario",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="votos_apuestas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Voto",
                "verbose_name_plural": "Votos",
                "unique_together": {("apuesta", "usuario")},
            },
        ),
    ]
