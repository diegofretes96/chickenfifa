import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Equipo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=100, verbose_name="nombre")),
                ("codigo_fifa", models.CharField(
                    help_text="Código ISO de 3 letras. Ej: ARG, BRA, ESP",
                    max_length=3,
                    unique=True,
                    verbose_name="código FIFA",
                )),
                ("grupo", models.CharField(
                    choices=[
                        ("A", "Grupo A"), ("B", "Grupo B"), ("C", "Grupo C"),
                        ("D", "Grupo D"), ("E", "Grupo E"), ("F", "Grupo F"),
                        ("G", "Grupo G"), ("H", "Grupo H"), ("I", "Grupo I"),
                        ("J", "Grupo J"), ("K", "Grupo K"), ("L", "Grupo L"),
                    ],
                    db_index=True,
                    max_length=1,
                    verbose_name="grupo",
                )),
                ("confederacion", models.CharField(
                    choices=[
                        ("UEFA", "UEFA (Europa)"),
                        ("CONMEBOL", "CONMEBOL (Sudamérica)"),
                        ("CONCACAF", "CONCACAF (América del Norte/Centro/Caribe)"),
                        ("CAF", "CAF (África)"),
                        ("AFC", "AFC (Asia)"),
                        ("OFC", "OFC (Oceanía)"),
                    ],
                    max_length=20,
                    verbose_name="confederación",
                )),
                ("bandera", models.ImageField(blank=True, null=True, upload_to="banderas/", verbose_name="bandera")),
                ("partidos_jugados", models.PositiveSmallIntegerField(default=0, verbose_name="PJ")),
                ("victorias", models.PositiveSmallIntegerField(default=0, verbose_name="G")),
                ("empates", models.PositiveSmallIntegerField(default=0, verbose_name="E")),
                ("derrotas", models.PositiveSmallIntegerField(default=0, verbose_name="P")),
                ("goles_favor", models.PositiveSmallIntegerField(default=0, verbose_name="GF")),
                ("goles_contra", models.PositiveSmallIntegerField(default=0, verbose_name="GC")),
                ("puntos_grupo", models.PositiveSmallIntegerField(default=0, verbose_name="Pts")),
                ("posicion_grupo", models.PositiveSmallIntegerField(
                    default=0,
                    help_text="1=primero, 2=segundo, 3=tercero, 4=cuarto",
                    verbose_name="posición en grupo",
                )),
                ("clasifico", models.BooleanField(default=False, verbose_name="clasificó a fase eliminatoria")),
            ],
            options={
                "verbose_name": "equipo",
                "verbose_name_plural": "equipos",
                "ordering": ["grupo", "posicion_grupo", "nombre"],
            },
        ),
        migrations.CreateModel(
            name="Partido",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("numero_partido", models.PositiveSmallIntegerField(
                    help_text="Numeración oficial FIFA (1–104)",
                    unique=True,
                    verbose_name="N° de partido",
                )),
                ("fase", models.CharField(
                    choices=[
                        ("grupo", "Fase de Grupos"),
                        ("dieciseisavos", "Dieciseisavos de Final"),
                        ("octavos", "Octavos de Final"),
                        ("cuartos", "Cuartos de Final"),
                        ("semifinal", "Semifinal"),
                        ("tercero", "Tercer Puesto"),
                        ("final", "Final"),
                    ],
                    db_index=True,
                    max_length=20,
                    verbose_name="fase",
                )),
                ("grupo", models.CharField(
                    blank=True,
                    choices=[
                        ("A", "Grupo A"), ("B", "Grupo B"), ("C", "Grupo C"),
                        ("D", "Grupo D"), ("E", "Grupo E"), ("F", "Grupo F"),
                        ("G", "Grupo G"), ("H", "Grupo H"), ("I", "Grupo I"),
                        ("J", "Grupo J"), ("K", "Grupo K"), ("L", "Grupo L"),
                    ],
                    help_text="Solo para partidos de fase de grupos",
                    max_length=1,
                    null=True,
                    verbose_name="grupo",
                )),
                ("equipo_local", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="partidos_local",
                    to="tournament.equipo",
                    verbose_name="equipo local",
                )),
                ("equipo_visitante", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="partidos_visitante",
                    to="tournament.equipo",
                    verbose_name="equipo visitante",
                )),
                ("placeholder_local", models.CharField(
                    blank=True,
                    help_text="Ej: 'Ganador Partido 37' o '1° Grupo A'",
                    max_length=60,
                    verbose_name="placeholder local",
                )),
                ("placeholder_visitante", models.CharField(blank=True, max_length=60, verbose_name="placeholder visitante")),
                ("goles_local", models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="goles local")),
                ("goles_visitante", models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="goles visitante")),
                ("penales_local", models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="penales local")),
                ("penales_visitante", models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="penales visitante")),
                ("fecha_hora", models.DateTimeField(db_index=True, verbose_name="fecha y hora (UTC)")),
                ("sede", models.CharField(blank=True, max_length=100, verbose_name="sede")),
                ("ciudad", models.CharField(blank=True, max_length=80, verbose_name="ciudad")),
                ("finalizado", models.BooleanField(db_index=True, default=False, verbose_name="finalizado")),
            ],
            options={
                "verbose_name": "partido",
                "verbose_name_plural": "partidos",
                "ordering": ["fecha_hora", "numero_partido"],
            },
        ),
        migrations.AddIndex(
            model_name="partido",
            index=models.Index(fields=["fase", "finalizado"], name="tournament__fase_fec_idx"),
        ),
        migrations.AddIndex(
            model_name="partido",
            index=models.Index(fields=["fase", "grupo"], name="tournament__fase_grp_idx"),
        ),
    ]
