import logging
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

from django.conf import settings
from django.shortcuts import redirect, render

try:
    from vercel.blob import BlobError
    from vercel.blob.sync import delete_blob, put_blob
except ImportError:  # Vercel Blob solo se necesita en producción; en local no es obligatorio
    class BlobError(Exception):
        pass

    put_blob = None
    delete_blob = None

# Create your views here.
from django.contrib import messages

from . import api_client
from .api_client import ApiError
from .decorators import admin_required, refresh_session_user

logger = logging.getLogger(__name__)
MAX_IMAGE_SIZE = 4 * 1024 * 1024
CART_SESSION_KEY = "carrito"
CART_COUNT_SESSION_KEY = "carrito_cantidad"


class ImageStorageError(Exception):
    pass


def _validate_product_image(image):
    extension = Path(image.name).suffix.lower()
    header = image.read(12)
    image.seek(0)

    valid_signatures = {
        ".jpg": header.startswith(b"\xff\xd8\xff"),
        ".jpeg": header.startswith(b"\xff\xd8\xff"),
        ".png": header.startswith(b"\x89PNG\r\n\x1a\n"),
        ".webp": header[:4] == b"RIFF" and header[8:12] == b"WEBP",
    }

    if image.size > MAX_IMAGE_SIZE:
        raise ValueError("La imagen no puede superar los 4 MB")
    if extension not in valid_signatures or not valid_signatures[extension]:
        raise ValueError("Sube una imagen JPG, PNG o WebP válida")
    return extension


def _catalog_image_url(image_url):
    prefix = f"{settings.MEDIA_URL}productos/"
    if image_url and image_url.startswith(prefix):
        filename = image_url[len(prefix):]
        if Path(filename).name == filename:
            static_image = Path(__file__).parent / "static" / "store" / "productos" / filename
            if static_image.is_file():
                return f"{settings.STATIC_URL}store/productos/{filename}"
    return image_url


def _get_cart(request):
    cart = request.session.get(CART_SESSION_KEY, {})
    if not isinstance(cart, dict):
        return {}
    return {
        str(product_id): quantity
        for product_id, quantity in cart.items()
        if isinstance(quantity, int) and not isinstance(quantity, bool) and quantity > 0
    }


def _save_cart(request, cart):
    cart = {
        str(product_id): quantity
        for product_id, quantity in cart.items()
        if isinstance(quantity, int) and not isinstance(quantity, bool) and quantity > 0
    }
    request.session[CART_SESSION_KEY] = cart
    request.session[CART_COUNT_SESSION_KEY] = sum(cart.values())


def _cart_page_items(cart):
    items = []
    for product_id, quantity in cart.items():
        try:
            product = api_client.obtener_producto(product_id)
        except ApiError as exc:
            items.append({
                "id": product_id,
                "quantity": quantity,
                "error": exc.detail,
            })
            continue
        product["quantity"] = quantity
        product["subtotal"] = product["precio"] * quantity
        items.append(product)
    return items


def catalogo(request):
    refresh_session_user(request)
    categoria = request.GET.get("categoria") or None
    try:
        productos = api_client.listar_productos(categoria)
    except ApiError as e:
        messages.error(request, e.detail)
        productos = []
    for product in productos:
        product["imagen_url"] = _catalog_image_url(product.get("imagen_url"))
    try:
        total_productos = api_client.contar_productos()
    except ApiError as e:
        messages.error(request, f"No se pudo cargar el total de productos: {e.detail}")
        total_productos = None
    return render(request, "catalogo.html",
                  {
                      "productos": productos,
                      "categoria": categoria or "",
                      "total_productos": total_productos,
                  })


def login_view(request):
    if request.session.get("token"):
        return redirect("catalogo")
    if request.method == "POST":
        rol_elegido = request.POST.get("rol", "cliente")
        try:
            data = api_client.login(
                request.POST.get("email", "").strip(),
                request.POST.get("password", ""),
            )
        except ApiError as e:
            messages.error(request, e.detail)
        else:
            rol_real = data["usuario"]["rol"]
            if rol_elegido != rol_real:
                if rol_elegido == "administrador":
                    messages.error(request, "Esta cuenta no tiene permisos de administrador")
                else:
                    messages.error(request, "Esta cuenta es de administrador: elige 'Administrador' para entrar")
            else:
                request.session["token"] = data["access_token"]
                request.session["usuario"] = data["usuario"]
                messages.success(request, f"Bienvenido, {data['usuario']['nombre']}")
                return redirect("panel_admin" if rol_real == "administrador" else "catalogo")
    return render(request, "login.html")

def registro_view(request):
    if request.method == "POST":
        try:
            api_client.registro(
                request.POST.get("nombre", "").strip(),
                request.POST.get("email", "").strip(),
                request.POST.get("password", ""),
            )
        except ApiError as e:
            messages.error(request, e.detail)
        else:
            messages.success(request, "Cuenta creada. Ya puedes iniciar sesión.")
            return redirect("login")
    return render(request, "registro.html")


def logout_view(request):
    request.session.flush()       # borra token y datos de la sesión
    messages.info(request, "Sesión cerrada")
    return redirect("catalogo")


def carrito(request):
    cart = _get_cart(request)
    items = _cart_page_items(cart)
    total = sum(item.get("subtotal", 0) for item in items)
    return render(request, "carrito.html", {"items": items, "total": total})


def carrito_agregar(request, producto_id):
    if request.method != "POST":
        return redirect("catalogo")
    try:
        product = api_client.obtener_producto(producto_id)
        quantity = int(request.POST.get("cantidad", "1"))
    except ValueError:
        messages.error(request, "La cantidad debe ser un número entero")
        return redirect("catalogo")
    except ApiError as exc:
        messages.error(request, exc.detail)
        return redirect("catalogo")

    cart = _get_cart(request)
    new_quantity = cart.get(producto_id, 0) + quantity
    if quantity < 1:
        messages.error(request, "La cantidad debe ser al menos 1")
    elif product["stock"] < new_quantity:
        messages.error(request, f"Solo hay {product['stock']} unidades disponibles de {product['nombre']}")
    else:
        cart[producto_id] = new_quantity
        _save_cart(request, cart)
        messages.success(request, f"{product['nombre']} se agregó al carrito")
    return redirect("catalogo")


def carrito_actualizar(request):
    if request.method != "POST":
        return redirect("carrito")
    product_id = request.POST.get("producto_id", "")
    try:
        quantity = int(request.POST.get("cantidad", "0"))
        if quantity < 0:
            raise ValueError
    except ValueError:
        messages.error(request, "La cantidad debe ser un número entero igual o mayor que cero")
        return redirect("carrito")

    cart = _get_cart(request)
    if product_id not in cart:
        messages.error(request, "Ese producto ya no está en el carrito")
        return redirect("carrito")
    if quantity == 0:
        cart.pop(product_id)
        _save_cart(request, cart)
        messages.info(request, "Producto eliminado del carrito")
        return redirect("carrito")

    try:
        product = api_client.obtener_producto(product_id)
    except ApiError as exc:
        messages.error(request, exc.detail)
        return redirect("carrito")
    if quantity > product["stock"]:
        messages.error(request, f"Solo hay {product['stock']} unidades disponibles de {product['nombre']}")
        return redirect("carrito")

    cart[product_id] = quantity
    _save_cart(request, cart)
    messages.success(request, "Carrito actualizado")
    return redirect("carrito")


def carrito_eliminar(request, producto_id):
    if request.method != "POST":
        return redirect("carrito")
    cart = _get_cart(request)
    cart.pop(producto_id, None)
    _save_cart(request, cart)
    messages.info(request, "Producto eliminado del carrito")
    return redirect("carrito")


def carrito_confirmar(request):
    token = request.session.get("token")
    if not token:
        messages.warning(request, "Inicia sesión para confirmar tu compra")
        return redirect("login")
    if request.method != "POST":
        return redirect("carrito")

    cart = _get_cart(request)
    if not cart:
        messages.error(request, "Tu carrito está vacío")
        return redirect("carrito")

    address = request.POST.get("direccion_envio", "").strip()
    if len(address) < 5:
        messages.error(request, "Escribe una dirección de envío válida")
        return redirect("carrito")

    order = {
        "direccion_envio": address,
        "items": [
            {"producto_id": product_id, "cantidad": quantity}
            for product_id, quantity in cart.items()
        ],
    }
    try:
        result = api_client.crear_pedido(order, token)
    except ApiError as exc:
        if exc.status == 401:
            request.session.flush()
            _save_cart(request, cart)
            messages.warning(request, "Tu sesión venció. Inicia sesión para confirmar la compra.")
            return redirect("login")
        messages.error(request, exc.detail)
        return redirect("carrito")

    request.session.pop(CART_SESSION_KEY, None)
    request.session.pop(CART_COUNT_SESSION_KEY, None)
    messages.success(request, f"Pedido confirmado. Número de pedido: {result['id']}")
    return redirect("carrito")


@admin_required
def producto_nuevo(request):
    if request.method == "POST":
        image = request.FILES.get("imagen")
        if image is None:
            messages.error(request, "Selecciona una imagen para el producto")
            return render(request, "producto_form.html")
        try:
            extension = _validate_product_image(image)
        except ValueError as exc:
            messages.error(request, str(exc))
            return render(request, "producto_form.html")

        try:
            datos = {
                "nombre": request.POST.get("nombre", "").strip(),
                "descripcion": request.POST.get("descripcion", "").strip(),
                "precio": float(request.POST.get("precio", "0")),
                "stock": int(request.POST.get("stock", "0")),
                "categoria": request.POST.get("categoria", "").strip(),
                "imagen_url": None,
            }
        except ValueError:
            messages.error(request, "Precio y stock deben ser números")
            return render(request, "producto_form.html")

        try:
            image_ref = _save_product_image(image, extension)
        except (OSError, ImageStorageError) as exc:
            logger.error("No se pudo guardar la imagen del producto: %s", exc)
            messages.error(request, f"No se pudo guardar la imagen: {exc}")
            return render(request, "producto_form.html")
        datos["imagen_url"] = _image_url(image_ref)
        try:
            api_client.crear_producto(datos)
        except ApiError as e:
            try:
                _delete_product_image(image_ref)
            except (OSError, ImageStorageError):
                logger.exception("No se pudo limpiar la imagen del producto rechazado")
            messages.error(request, e.detail)
        else:
            messages.success(request, "Producto creado correctamente")
            return redirect("catalogo")
    return render(request, "producto_form.html")


def _save_product_image(image, extension):
    if settings.BLOB_STORAGE_CONFIGURED:
        if put_blob is None:
            raise ImageStorageError("Falta instalar el paquete de Vercel Blob (pip install vercel).")
        image.seek(0)
        content_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
        }
        try:
            result = put_blob(
                f"productos/{uuid4().hex}{extension}",
                image.read(),
                access="public",
                content_type=content_types[extension],
                add_random_suffix=True,
            )
        except BlobError as exc:
            logger.exception("Vercel Blob no pudo guardar la imagen")
            raise ImageStorageError("Vercel Blob rechazó la carga. Verifica el almacén público y sus credenciales.") from exc
        return result.url
    if not settings.DEBUG:
        raise ImageStorageError("Configura Vercel Blob antes de subir imágenes en producción.")

    image_directory = settings.MEDIA_ROOT / "productos"
    image_directory.mkdir(parents=True, exist_ok=True)
    image_path = image_directory / f"{uuid4().hex}{extension}"
    with image_path.open("wb") as destination:
        for chunk in image.chunks():
            destination.write(chunk)
    return image_path


def _image_url(image_path):
    if isinstance(image_path, str):
        return image_path
    return f"{settings.MEDIA_URL}productos/{image_path.name}"


def _local_product_image(image_url):
    prefix = f"{settings.MEDIA_URL}productos/"
    if not image_url or not image_url.startswith(prefix):
        return None

    filename = image_url[len(prefix):]
    if not filename or Path(filename).name != filename:
        return None
    return settings.MEDIA_ROOT / "productos" / filename


def _delete_file(path):
    if path and path.is_file():
        path.unlink()


def _delete_product_image(image_ref):
    if not image_ref:
        return
    if isinstance(image_ref, Path):
        _delete_file(image_ref)
        return

    parsed = urlparse(image_ref)
    if parsed.scheme == "https" and parsed.hostname and parsed.hostname.endswith(".blob.vercel-storage.com"):
        pathname = parsed.path.lstrip("/")
        if not pathname.startswith("productos/") or ".." in Path(pathname).parts:
            raise ImageStorageError("La ruta de la imagen en Blob no es válida.")
        if delete_blob is None:
            raise ImageStorageError("Falta instalar el paquete de Vercel Blob (pip install vercel).")
        try:
            delete_blob(pathname)
        except BlobError as exc:
            logger.exception("Vercel Blob no pudo eliminar la imagen")
            raise ImageStorageError("No se pudo eliminar la imagen de Vercel Blob.") from exc
        return

    _delete_file(_local_product_image(image_ref))


def _product_form(request, product=None):
    context = {"product": product}
    if request.method != "POST":
        return render(request, "producto_form.html", context)

    image = request.FILES.get("imagen")
    extension = None
    if image:
        try:
            extension = _validate_product_image(image)
        except ValueError as exc:
            messages.error(request, str(exc))
            return render(request, "producto_form.html", context)
    elif product is None:
        messages.error(request, "Selecciona una imagen para el producto")
        return render(request, "producto_form.html", context)

    try:
        datos = {
            "nombre": request.POST.get("nombre", "").strip(),
            "descripcion": request.POST.get("descripcion", "").strip(),
            "precio": float(request.POST.get("precio", "0")),
            "stock": int(request.POST.get("stock", "0")),
            "categoria": request.POST.get("categoria", "").strip(),
        }
    except ValueError:
        messages.error(request, "Precio y stock deben ser números")
        return render(request, "producto_form.html", context)

    new_image_path = None
    if image:
        try:
            new_image_path = _save_product_image(image, extension)
        except (OSError, ImageStorageError) as exc:
            logger.error("No se pudo guardar la imagen del producto: %s", exc)
            messages.error(request, f"No se pudo guardar la imagen: {exc}")
            return render(request, "producto_form.html", context)
        datos["imagen_url"] = _image_url(new_image_path)
    elif product is not None:
        datos["imagen_url"] = product.get("imagen_url")

    try:
        if product is None:
            api_client.crear_producto(datos)
        else:
            api_client.actualizar_producto(product["id"], datos)
    except ApiError as exc:
        if new_image_path:
            try:
                _delete_product_image(new_image_path)
            except (OSError, ImageStorageError):
                logger.exception("No se pudo limpiar la imagen del producto rechazado")
        messages.error(request, exc.detail)
        return render(request, "producto_form.html", context)

    if new_image_path and product is not None:
        try:
            _delete_product_image(product.get("imagen_url"))
        except (OSError, ImageStorageError):
            logger.exception("No se pudo limpiar la imagen anterior del producto")
            messages.warning(request, "El producto se actualizó, pero no se pudo borrar su imagen anterior.")
    messages.success(
        request,
        "Producto creado correctamente" if product is None else "Producto actualizado correctamente",
    )
    return redirect("catalogo")


@admin_required
def producto_editar(request, producto_id):
    try:
        product = api_client.obtener_producto(producto_id)
    except ApiError as exc:
        messages.error(request, exc.detail)
        return redirect("catalogo")
    product["imagen_url"] = _catalog_image_url(product.get("imagen_url"))
    return _product_form(request, product)


@admin_required
def productos_seleccionados(request):
    if request.method != "POST":
        return redirect("catalogo")

    product_ids = list(dict.fromkeys(request.POST.getlist("producto_ids")))
    action = request.POST.get("action")
    if not product_ids:
        messages.error(request, "Selecciona al menos un producto")
        return redirect("catalogo")

    if action == "edit":
        if len(product_ids) != 1:
            messages.error(request, "Selecciona exactamente un producto para editar")
            return redirect("catalogo")
        return redirect("producto_editar", producto_id=product_ids[0])

    if action != "delete":
        messages.error(request, "Acción de productos no válida")
        return redirect("catalogo")

    deleted = 0
    errors = []
    for product_id in product_ids:
        try:
            product = api_client.obtener_producto(product_id)
            api_client.eliminar_producto(product_id)
        except ApiError as exc:
            errors.append(f"{product_id}: {exc.detail}")
            continue

        try:
            _delete_product_image(product.get("imagen_url"))
        except (OSError, ImageStorageError) as exc:
            logger.exception("No se pudo eliminar la imagen del producto %s", product_id)
            errors.append(f"No se pudo eliminar la imagen de {product.get('nombre', product_id)}: {exc}")
        deleted += 1

    if deleted:
        messages.success(request, f"Se eliminaron {deleted} producto(s)")
    for error in errors:
        messages.error(request, error)
    return redirect("catalogo")


@admin_required
def panel_admin(request):
    return render(request, "panel_admin.html")