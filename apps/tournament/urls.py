from django.urls import path

from apps.tournament import views

app_name = "tournament"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("grupos/", views.grupos, name="grupos"),
    path("bracket/", views.bracket, name="bracket"),
    path("partido/<int:pk>/", views.detalle_partido, name="detalle_partido"),
]
