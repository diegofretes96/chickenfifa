from django.urls import path

from . import views

app_name = "bets"

urlpatterns = [
    path("", views.lista_apuestas, name="lista"),
    path("<int:pk>/votar/", views.votar, name="votar"),
]
