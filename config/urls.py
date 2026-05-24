from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("cuentas/", include("apps.accounts.urls", namespace="accounts")),
    path("torneo/", include("apps.tournament.urls", namespace="tournament")),
    path("pronosticos/", include("apps.predictions.urls", namespace="predictions")),
    path("clasificacion/", include("apps.leaderboard.urls", namespace="leaderboard")),
    path("", include("apps.tournament.urls_home")),
]

if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
