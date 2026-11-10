from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect

from . import api_client
from .api_client import ApiError


def refresh_session_user(request):
    token = request.session.get("token")
    if not token:
        request.session.pop("usuario", None)
        return True
    try:
        usuario = api_client.perfil(token)
    except ApiError as exc:
        if exc.status == 401:
            request.session.flush()
            messages.warning(request, "Tu sesión venció. Inicia sesión de nuevo.")
        else:
            request.session.pop("usuario", None)
            messages.error(request, f"No se pudo validar la sesión: {exc.detail}")
        return False

    request.session["usuario"] = usuario
    return True


def admin_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not refresh_session_user(request):
            return redirect("login" if not request.session.get("token") else "catalogo")
        usuario = request.session.get("usuario")
        if not usuario:
            messages.warning(request, "Inicia sesión para continuar")
            return redirect("login")
        if usuario.get("rol") != "administrador":
            messages.error(request, "No tienes permisos de administrador")
            return redirect("catalogo")
        return view(request, *args, **kwargs)
    return wrapper