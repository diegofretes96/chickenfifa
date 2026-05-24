import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("tournament", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Pronostico",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("usuario", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="pronosticos",
                    to=settings.AUTH_USER_MODEL,
                    verbose_name="usuario",
                )),
                ("partido", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="pronosticos",
                    to="tournament.partido",
                    verbose_name="partido",
                )),
                ("goles_local", models.PositiveSmallIntegerField(verbose_name="goles local pronosticados")),
                ("goles_visitante", models.PositiveSmallIntegerField(verbose_name="goles visitante pronosticados")),
                ("puntos_otorgados", models.PositiveSmallIntegerField(
                    blank=True,
                    help_text="Se calcula automáticamente al registrar el resultado oficial",
                    null=True,
                    verbose_name="puntos otorgados",
                )),
                ("detalle_puntos", models.JSONField(
                    blank=True,
                    help_text="Desglose del cálculo: {'exacto': bool, 'resultado': bool, 'puntos': int}",
                    null=True,
                    verbose_name="detalle de puntos",
                )),
                ("creado_en", models.DateTimeField(auto_now_add=True, verbose_name="creado en")),
                ("actualizado_en", models.DateTimeField(auto_now=True, verbose_name="actualizado en")),
            ],
            options={
                "verbose_name": "pronóstico",
                "verbose_name_plural": "pronósticos",
                "ordering": ["partido__fecha_hora"],
            },
        ),
        migrations.CreateModel(
            name="PronosticoClasificacion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("usuario", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="pronosticos_clasificacion",
                    to=settings.AUTH_USER_MODEL,
                    verbose_name="usuario",
                )),
                ("partido", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="pronosticos_clasificacion",
                    to="tournament.partido",
                    verbose_name="partido eliminatorio",
                )),
                ("equipo_elegido", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="pronosticos_como_clasificado",
                    to="tournament.equipo",
                    verbose_name="equipo elegido para clasificar",
                )),
                ("puntos_otorgados", models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="puntos otorgados")),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "pronóstico de clasificación",
                "verbose_name_plural": "pronósticos de clasificación",
                "ordering": ["partido__fecha_hora"],
            },
        ),
        migrations.AlterUniqueTogether(
            name="pronostico",
            unique_together={("usuario", "partido")},
        ),
        migrations.AddIndex(
            model_name="pronostico",
            index=models.Index(fields=["usuario", "partido"], name="predictions__user_partido_idx"),
        ),
        migrations.AddIndex(
            model_name="pronostico",
            index=models.Index(fields=["partido", "puntos_otorgados"], name="predictions__partido_pts_idx"),
        ),
        migrations.AlterUniqueTogether(
            name="pronosticoclasificacion",
            unique_together={("usuario", "partido")},
        ),
    ]
