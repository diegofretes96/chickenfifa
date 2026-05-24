from django.contrib.auth import views as auth_views
from django.urls import path

from apps.accounts import views

app_name = "accounts"

urlpatterns = [
    path("registro/", views.registro, name="registro"),
    path("iniciar-sesion/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("cerrar-sesion/", auth_views.LogoutView.as_view(), name="logout"),
    path("perfil/", views.perfil, name="perfil"),
    path("mis-grupos/", views.mis_grupos, name="mis_grupos"),
    path("mis-grupos/unirse/", views.unirse_grupo, name="unirse_grupo"),
    path("mis-grupos/crear/", views.crear_grupo, name="crear_grupo"),
    path("mis-grupos/<int:pk>/", views.detalle_grupo, name="detalle_grupo"),
    # Recuperación de contraseña (Django built-in)
    path("password/reset/", auth_views.PasswordResetView.as_view(
        template_name="accounts/password_reset.html",
        email_template_name="accounts/password_reset_email.html",
        subject_template_name="accounts/password_reset_subject.txt",
    ), name="password_reset"),
    path("password/reset/enviado/", auth_views.PasswordResetDoneView.as_view(
        template_name="accounts/password_reset_done.html",
    ), name="password_reset_done"),
    path("password/reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="accounts/password_reset_confirm.html",
    ), name="password_reset_confirm"),
    path("password/reset/completo/", auth_views.PasswordResetCompleteView.as_view(
        template_name="accounts/password_reset_complete.html",
    ), name="password_reset_complete"),
]
