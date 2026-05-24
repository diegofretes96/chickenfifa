from django.urls import path

from apps.leaderboard import views

app_name = "leaderboard"

urlpatterns = [
    path("", views.clasificacion_global, name="global"),
    path("grupo/<int:pk>/", views.clasificacion_grupo, name="grupo"),
]
