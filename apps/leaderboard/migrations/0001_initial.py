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
            name="SnapshotClasificacion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("usuario", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="snapshots_clasificacion",
                    to=settings.AUTH_USER_MODEL,
                    verbose_name="usuario",
                )),
                ("posicion", models.PositiveIntegerField(verbose_name="posición")),
                ("posicion_anterior", models.PositiveIntegerField(blank=True, null=True, verbose_name="posición anterior")),
                ("puntos", models.IntegerField(verbose_name="puntos")),
                ("puntos_exactos", models.PositiveIntegerField(default=0, verbose_name="pronósticos exactos")),
                ("puntos_resultado", models.PositiveIntegerField(default=0, verbose_name="pronósticos resultado correcto")),
                ("fecha", models.DateField(auto_now_add=True, db_index=True, verbose_name="fecha")),
                ("generado_en", models.DateTimeField(auto_now=True, verbose_name="generado en")),
            ],
            options={
                "verbose_name": "snapshot de clasificación",
                "verbose_name_plural": "snapshots de clasificación",
                "ordering": ["posicion"],
                "get_latest_by": "generado_en",
                "unique_together": {("usuario", "fecha")},
            },
        ),
    ]
