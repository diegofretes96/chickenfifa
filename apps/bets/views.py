from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Apuesta, VotoApuesta


def lista_apuestas(request):
    apuestas = Apuesta.objects.all()
    voto_usuario = {}
    if request.user.is_authenticated:
        votos = VotoApuesta.objects.filter(usuario=request.user).select_related("apuesta")
        voto_usuario = {v.apuesta_id: v for v in votos}
    return render(request, "bets/lista.html", {
        "apuestas": apuestas,
        "voto_usuario": voto_usuario,
        "ahora": timezone.now(),
    })


@login_required
def votar(request, pk):
    apuesta = get_object_or_404(Apuesta, pk=pk)

    if timezone.now() >= apuesta.fecha_limite:
        messages.error(request, "El tiempo para apostar ya cerró.")
        return redirect("bets:lista")

    if VotoApuesta.objects.filter(apuesta=apuesta, usuario=request.user).exists():
        messages.warning(request, "Ya registraste tu apuesta.")
        return redirect("bets:lista")

    opcion = request.POST.get("opcion")
    if opcion not in ("A", "B"):
        messages.error(request, "Opción inválida.")
        return redirect("bets:lista")

    VotoApuesta.objects.create(apuesta=apuesta, usuario=request.user, opcion=opcion)
    nombre_opcion = apuesta.opcion_a if opcion == "A" else apuesta.opcion_b
    messages.success(request, f"Apuesta registrada: {nombre_opcion}")
    return redirect("bets:lista")
