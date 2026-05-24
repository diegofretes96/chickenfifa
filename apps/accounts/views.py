from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.forms import CrearGrupoForm, PerfilForm, RegistroForm, UnirseGrupoForm
from apps.accounts.models import GrupoPolla


def registro(request):
    if request.user.is_authenticated:
        return redirect("tournament:inicio")
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"¡Bienvenido, {user.username}! Tu cuenta fue creada.")
            return redirect("tournament:inicio")
    else:
        form = RegistroForm()
    return render(request, "accounts/registro.html", {"form": form})


@login_required
def perfil(request):
    perfil_obj = request.user.perfil
    if request.method == "POST":
        form = PerfilForm(request.POST, request.FILES, instance=perfil_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect("accounts:perfil")
    else:
        form = PerfilForm(instance=perfil_obj)
    return render(request, "accounts/perfil.html", {"form": form, "perfil": perfil_obj})


@login_required
def mis_grupos(request):
    grupos_miembro = request.user.grupos_polla.all()
    grupos_creados = request.user.grupos_creados.all()
    unirse_form = UnirseGrupoForm()
    crear_form = CrearGrupoForm()
    return render(request, "accounts/mis_grupos.html", {
        "grupos_miembro": grupos_miembro,
        "grupos_creados": grupos_creados,
        "unirse_form": unirse_form,
        "crear_form": crear_form,
    })


@login_required
def unirse_grupo(request):
    if request.method == "POST":
        form = UnirseGrupoForm(request.POST)
        if form.is_valid():
            grupo = form.cleaned_data["codigo"]
            grupo.miembros.add(request.user)
            messages.success(request, f"Te uniste al grupo «{grupo.nombre}».")
        else:
            messages.error(request, "Código inválido.")
    return redirect("accounts:mis_grupos")


@login_required
def crear_grupo(request):
    if request.method == "POST":
        form = CrearGrupoForm(request.POST)
        if form.is_valid():
            grupo = form.save(commit=False)
            grupo.creador = request.user
            grupo.save()
            grupo.miembros.add(request.user)
            messages.success(request, f"Grupo «{grupo.nombre}» creado. Código: {grupo.codigo_invitacion}")
    return redirect("accounts:mis_grupos")


@login_required
def detalle_grupo(request, pk):
    grupo = get_object_or_404(GrupoPolla, pk=pk)
    ranking = grupo.ranking_interno()
    return render(request, "accounts/detalle_grupo.html", {"grupo": grupo, "ranking": ranking})
