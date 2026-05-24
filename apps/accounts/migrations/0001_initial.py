import apps.accounts.models
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PerfilUsuario",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("usuario", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="perfil",
                    to=settings.AUTH_USER_MODEL,
                    verbose_name="usuario",
                )),
                ("nombre_display", models.CharField(
                    blank=True,
                    help_text="Alias público en la tabla de clasificación",
                    max_length=50,
                    verbose_name="nombre a mostrar",
                )),
                ("avatar", models.ImageField(blank=True, null=True, upload_to="avatares/", verbose_name="avatar")),
                ("puntos_totales", models.IntegerField(db_index=True, default=0, verbose_name="puntos totales")),
                ("fecha_registro", models.DateTimeField(auto_now_add=True, verbose_name="fecha de registro")),
                ("bio", models.CharField(blank=True, max_length=200, verbose_name="bio")),
            ],
            options={
                "verbose_name": "perfil de usuario",
                "verbose_name_plural": "perfiles de usuario",
                "ordering": ["-puntos_totales"],
            },
        ),
        migrations.CreateModel(
            name="GrupoPolla",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=80, verbose_name="nombre del grupo")),
                ("codigo_invitacion", models.CharField(
                    default=apps.accounts.models._generar_codigo_invitacion,
                    editable=False,
                    max_length=8,
                    unique=True,
                    verbose_name="código de invitación",
                )),
                ("creador", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="grupos_creados",
                    to=settings.AUTH_USER_MODEL,
                    verbose_name="creador",
                )),
                ("miembros", models.ManyToManyField(
                    blank=True,
                    related_name="grupos_polla",
                    to=settings.AUTH_USER_MODEL,
                    verbose_name="miembros",
                )),
                ("descripcion", models.TextField(blank=True, verbose_name="descripción")),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True, verbose_name="fecha de creación")),
                ("es_publico", models.BooleanField(
                    default=False,
                    help_text="Si es público, aparece en el listado de grupos sin necesitar código",
                    verbose_name="grupo público",
                )),
            ],
            options={
                "verbose_name": "grupo polla",
                "verbose_name_plural": "grupos polla",
                "ordering": ["nombre"],
            },
        ),
    ]
