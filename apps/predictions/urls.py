from django.urls import path

from apps.predictions import views

app_name = "predictions"

urlpatterns = [
    path("", views.mis_pronosticos, name="mis_pronosticos"),
    path("fase-de-grupos/", views.pronosticos_grupo, name="grupo"),
    path("eliminatoria/", views.pronosticos_eliminatoria, name="eliminatoria"),
    path("guardar/<int:partido_pk>/", views.guardar_pronostico, name="guardar"),
]
