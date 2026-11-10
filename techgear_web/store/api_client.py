import requests
from django.conf import settings

TIMEOUT = 60


class ApiError(Exception):
    def __init__(self, status, detail):
        super().__init__(detail)
        self.status = status
        self.detail = detail


def _request(method, path, token=None, api_key=None, **kwargs):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if api_key:
        headers["X-API-Key"] = api_key
    try:
        r = requests.request(
            method, f"{settings.API_URL}{path}",
            headers=headers, timeout=TIMEOUT, **kwargs,
        )
    except requests.RequestException:
        raise ApiError(503, "No se pudo conectar con la API de TechGear")
    if r.status_code >= 400:
        raise ApiError(r.status_code, _error_detail(r))
    if not r.content:
        return None
    try:
        return r.json()
    except ValueError:
        raise ApiError(502, "La API devolvió una respuesta que no es JSON")


def _error_detail(r):
    """Extrae el mensaje de error aunque la API responda texto plano (p. ej. un 500)."""
    if not r.content:
        return "Error"
    try:
        body = r.json()
    except ValueError:
        return f"Error {r.status_code} en la API"
    detail = body.get("detail", "Error en la API") if isinstance(body, dict) else "Error en la API"
    if isinstance(detail, list):          # error 422 de validación
        first = detail[0] if detail else {}
        detail = first.get("msg", "Datos inválidos") if isinstance(first, dict) else "Datos inválidos"
    return detail


def login(email, password):
    return _request("POST", "/usuarios/login", json={"email": email, "password": password})


def registro(nombre, email, password):
    return _request("POST", "/usuarios/registro",
                    json={"nombre": nombre, "email": email, "password": password})

def perfil(token):
    return _request("GET", "/usuarios/me", token=token)


def listar_productos(categoria=None):
    params = {"categoria": categoria} if categoria else {}
    return _request("GET", "/productos/", params=params)

def contar_productos():
    return _request("GET", "/productos/count")["total"]

def obtener_producto(producto_id):
    return _request("GET", f"/productos/{producto_id}")

def crear_producto(datos):
    return _request("POST", "/productos/", api_key=settings.API_KEY, json=datos)

def actualizar_producto(producto_id, datos):
    return _request(
        "PUT", f"/productos/{producto_id}",
        api_key=settings.API_KEY, json=datos,
    )

def eliminar_producto(producto_id):
    return _request(
        "DELETE", f"/productos/{producto_id}",
        api_key=settings.API_KEY,
    )

def crear_pedido(datos, token):
    return _request("POST", "/pedidos/", token=token, json=datos)