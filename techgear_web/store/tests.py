import base64
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

from . import api_client
from .api_client import ApiError


class ProductImageUploadTests(TestCase):
    png_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/lWQAAAAASUVORK5CYII="
    )

    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_directory.cleanup)
        override = override_settings(
            MEDIA_ROOT=Path(self.temp_directory.name),
            DEBUG=True,
            BLOB_STORAGE_CONFIGURED=False,
        )
        override.enable()
        self.addCleanup(override.disable)
        session = self.client.session
        session["token"] = "cached-client-token"
        session["usuario"] = {"rol": "cliente"}
        session.save()
        self.client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key
        profile_patcher = patch(
            "store.api_client.perfil",
            return_value={"rol": "administrador"},
        )
        profile_patcher.start()
        self.addCleanup(profile_patcher.stop)

    def product_data(self, image):
        return {
            "nombre": "Labial rosa",
            "descripcion": "Color suave para todos los días",
            "precio": "12000",
            "stock": "8",
            "categoria": "Maquillaje",
            "imagen": image,
        }

    @patch("store.views.api_client.crear_producto")
    def test_saves_uploaded_image_and_sends_media_path_to_api(self, create_product):
        image = SimpleUploadedFile("labial.png", self.png_data, content_type="image/png")
        response = self.client.post(
            "/panel/productos/nuevo/",
            self.product_data(image),
        )

        self.assertRedirects(response, "/")
        product = create_product.call_args.args[0]
        self.assertTrue(product["imagen_url"].startswith("/media/productos/"))
        stored_image = Path(self.temp_directory.name) / product["imagen_url"].removeprefix("/media/")
        self.assertTrue(stored_image.is_file())

    @override_settings(BLOB_STORAGE_CONFIGURED=True)
    @patch(
        "store.views.put_blob",
        return_value=SimpleNamespace(
            url="https://store.public.blob.vercel-storage.com/productos/labial.png"
        ),
    )
    @patch("store.views.api_client.crear_producto")
    def test_saves_uploaded_image_to_vercel_blob(self, create_product, upload_blob):
        image = SimpleUploadedFile("labial.png", self.png_data, content_type="image/png")
        response = self.client.post(
            reverse("producto_nuevo"),
            self.product_data(image),
        )

        self.assertRedirects(response, "/")
        self.assertEqual(
            create_product.call_args.args[0]["imagen_url"],
            "https://store.public.blob.vercel-storage.com/productos/labial.png",
        )
        self.assertEqual(upload_blob.call_args.kwargs["access"], "public")
        self.assertEqual(upload_blob.call_args.kwargs["content_type"], "image/png")

    @override_settings(DEBUG=False, BLOB_STORAGE_CONFIGURED=False)
    @patch("store.views.api_client.crear_producto")
    def test_production_upload_requires_blob_instead_of_local_disk(self, create_product):
        image = SimpleUploadedFile("labial.png", self.png_data, content_type="image/png")
        response = self.client.post(
            reverse("producto_nuevo"),
            self.product_data(image),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Configura Vercel Blob")
        create_product.assert_not_called()

    @patch("store.views.api_client.crear_producto")
    def test_rejects_non_image_upload(self, create_product):
        image = SimpleUploadedFile("not-image.png", b"not a png", content_type="image/png")
        response = self.client.post(
            "/panel/productos/nuevo/",
            self.product_data(image),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sube una imagen JPG, PNG o WebP válida")
        create_product.assert_not_called()

    @patch("store.views.api_client.crear_producto", side_effect=ApiError(401, "API key inválida"))
    def test_removes_image_when_api_rejects_product(self, create_product):
        image = SimpleUploadedFile("labial.png", self.png_data, content_type="image/png")
        response = self.client.post(
            "/panel/productos/nuevo/",
            self.product_data(image),
        )

        self.assertEqual(response.status_code, 200)
        stored_images = list((Path(self.temp_directory.name) / "productos").glob("*"))
        self.assertEqual(stored_images, [])
        create_product.assert_called_once()

    @patch("store.views.api_client.listar_productos", return_value=[])
    @patch("store.views.api_client.contar_productos", return_value=4)
    def test_catalog_menu_shows_total_product_count(self, count_products, list_products):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Productos (4)")

    @patch(
        "store.views.api_client.listar_productos",
        return_value=[{
            "id": "product-1",
            "nombre": "Labial rosa",
            "descripcion": "Color suave",
            "precio": 12000,
            "stock": 8,
            "categoria": "Maquillaje",
            "imagen_url": "/media/productos/labial-rosa.jpg",
        }],
    )
    @patch("store.views.api_client.contar_productos", return_value=4)
    def test_catalog_maps_bundled_product_images_to_static_urls(self, count_products, list_products):
        response = self.client.get(reverse("catalogo"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "/static/store/productos/labial-rosa.jpg")

    @patch(
        "store.views.api_client.listar_productos",
        return_value=[{
            "id": "product-1",
            "nombre": "Labial rosa",
            "descripcion": "Color suave",
            "precio": 12000,
            "stock": 8,
            "categoria": "Maquillaje",
            "imagen_url": "/media/productos/labial.jpg",
        }],
    )
    @patch("store.views.api_client.contar_productos", return_value=4)
    def test_admin_catalog_has_product_selection_actions(self, count_products, list_products):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="producto_ids"')
        self.assertContains(response, "Editar seleccionado")
        self.assertContains(response, "Eliminar seleccionados")

    @patch("store.api_client.perfil", side_effect=ApiError(401, "Token expirado"))
    @patch("store.views.api_client.listar_productos", return_value=[])
    @patch("store.views.api_client.contar_productos", return_value=4)
    def test_expired_session_hides_admin_controls(self, count_products, list_products, profile):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "productos_seleccionados")
        self.assertNotContains(response, "Nuevo producto")
        self.assertNotIn("usuario", self.client.session)

    @patch("store.views.api_client.obtener_producto")
    @patch("store.views.api_client.actualizar_producto")
    def test_edit_preserves_existing_image_when_no_replacement_is_uploaded(
        self,
        update_product,
        get_product,
    ):
        product = {
            "id": "product-1",
            "nombre": "Labial rosa",
            "descripcion": "Color suave",
            "precio": 12000,
            "stock": 8,
            "categoria": "Maquillaje",
            "imagen_url": "/media/productos/labial.jpg",
        }
        get_product.return_value = product
        response = self.client.post(
            reverse("producto_editar", args=[product["id"]]),
            {
                "nombre": "Labial rosa nuevo",
                "descripcion": "Color suave",
                "precio": "13000",
                "stock": "7",
                "categoria": "Maquillaje",
            },
        )

        self.assertRedirects(response, "/")
        update_product.assert_called_once()
        self.assertEqual(
            update_product.call_args.args[1]["imagen_url"],
            product["imagen_url"],
        )

    @patch("store.views.api_client.obtener_producto")
    def test_edit_selection_requires_exactly_one_product(self, get_product):
        response = self.client.post(
            reverse("productos_seleccionados"),
            {"action": "edit", "producto_ids": ["one", "two"]},
        )

        self.assertRedirects(response, "/")
        get_product.assert_not_called()

    @patch("store.views.api_client.obtener_producto")
    @patch("store.views.api_client.eliminar_producto")
    def test_delete_selection_removes_products(self, delete_product, get_product):
        get_product.side_effect = [
            {"id": "one", "nombre": "Labial", "imagen_url": None},
            {"id": "two", "nombre": "Serum", "imagen_url": None},
        ]
        response = self.client.post(
            reverse("productos_seleccionados"),
            {"action": "delete", "producto_ids": ["one", "two"]},
        )

        self.assertRedirects(response, "/")
        self.assertEqual(get_product.call_count, 2)
        self.assertEqual(delete_product.call_count, 2)

    @patch("store.views.delete_blob")
    @patch("store.views.api_client.obtener_producto")
    @patch("store.views.api_client.eliminar_producto")
    def test_delete_selection_removes_blob_image(self, delete_product, get_product, remove_blob):
        get_product.return_value = {
            "id": "product-1",
            "nombre": "Labial",
            "imagen_url": "https://store.public.blob.vercel-storage.com/productos/labial.png",
        }

        response = self.client.post(
            reverse("productos_seleccionados"),
            {"action": "delete", "producto_ids": ["product-1"]},
        )

        self.assertRedirects(response, "/")
        delete_product.assert_called_once_with("product-1")
        remove_blob.assert_called_once_with("productos/labial.png")


class CartTests(TestCase):
    product = {
        "id": "product-1",
        "nombre": "Labial rosa",
        "descripcion": "Color suave",
        "precio": 12000,
        "stock": 8,
        "categoria": "Maquillaje",
        "imagen_url": "/media/productos/labial.jpg",
    }

    def set_cart(self, cart, token=None):
        session = self.client.session
        session["carrito"] = cart
        session["carrito_cantidad"] = sum(cart.values())
        if token:
            session["token"] = token
            session["usuario"] = {"rol": "cliente"}
        session.save()
        self.client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key

    @patch("store.views.api_client.obtener_producto", return_value=product)
    def test_guest_can_add_and_update_product_quantity(self, get_product):
        response = self.client.post(
            reverse("carrito_agregar", args=[self.product["id"]]),
            {"cantidad": "2"},
        )

        self.assertRedirects(response, "/")
        self.assertEqual(self.client.session["carrito"], {"product-1": 2})
        self.assertEqual(self.client.session["carrito_cantidad"], 2)
        response = self.client.post(
            reverse("carrito_actualizar"),
            {"producto_id": "product-1", "cantidad": "3"},
        )

        self.assertRedirects(response, reverse("carrito"))
        self.assertEqual(self.client.session["carrito"], {"product-1": 3})
        self.assertEqual(self.client.session["carrito_cantidad"], 3)
        self.assertEqual(get_product.call_count, 3)

    @patch("store.views.api_client.obtener_producto", return_value=product)
    def test_add_rejects_quantity_above_available_stock(self, get_product):
        response = self.client.post(
            reverse("carrito_agregar", args=[self.product["id"]]),
            {"cantidad": "9"},
        )

        self.assertRedirects(response, "/")
        self.assertNotIn("carrito", self.client.session)

    def test_remove_product_updates_navigation_count(self):
        self.set_cart({"product-1": 2})

        response = self.client.post(
            reverse("carrito_eliminar", args=["product-1"]),
        )

        self.assertRedirects(response, reverse("carrito"))
        self.assertEqual(self.client.session["carrito"], {})
        self.assertEqual(self.client.session["carrito_cantidad"], 0)

    def test_guest_checkout_redirects_to_login_and_keeps_cart(self):
        self.set_cart({"product-1": 1})

        response = self.client.post(
            reverse("carrito_confirmar"),
            {"direccion_envio": "Calle 123"},
        )

        self.assertRedirects(response, reverse("login"))
        self.assertEqual(self.client.session["carrito"], {"product-1": 1})

    @patch("store.views.api_client.crear_pedido", side_effect=ApiError(409, "Stock insuficiente"))
    def test_checkout_failure_preserves_cart(self, create_order):
        self.set_cart({"product-1": 2}, token="client-token")

        response = self.client.post(
            reverse("carrito_confirmar"),
            {"direccion_envio": "Calle 123"},
        )

        self.assertRedirects(response, reverse("carrito"))
        self.assertEqual(self.client.session["carrito"], {"product-1": 2})
        create_order.assert_called_once_with(
            {
                "direccion_envio": "Calle 123",
                "items": [{"producto_id": "product-1", "cantidad": 2}],
            },
            "client-token",
        )

    @patch(
        "store.views.api_client.crear_pedido",
        return_value={"id": "order-1"},
    )
    def test_successful_checkout_clears_cart(self, create_order):
        self.set_cart({"product-1": 2}, token="client-token")

        response = self.client.post(
            reverse("carrito_confirmar"),
            {"direccion_envio": "Calle 123"},
        )

        self.assertRedirects(response, reverse("carrito"))
        self.assertNotIn("carrito", self.client.session)
        self.assertNotIn("carrito_cantidad", self.client.session)

    @patch("store.views.api_client.crear_pedido", side_effect=ApiError(401, "Token expirado"))
    def test_expired_checkout_session_keeps_cart_and_requires_login(self, create_order):
        self.set_cart({"product-1": 1}, token="expired-token")

        response = self.client.post(
            reverse("carrito_confirmar"),
            {"direccion_envio": "Calle 123"},
        )

        self.assertRedirects(response, reverse("login"))
        self.assertNotIn("token", self.client.session)
        self.assertEqual(self.client.session["carrito"], {"product-1": 1})

    @patch("store.views.api_client.obtener_producto", return_value=product)
    def test_cart_page_shows_product_subtotal_and_checkout(self, get_product):
        self.set_cart({"product-1": 2}, token="client-token")

        response = self.client.get(reverse("carrito"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Labial rosa")
        self.assertContains(response, "$24,000")
        self.assertContains(response, "Confirmar compra")

    @patch("store.views.api_client.contar_productos", return_value=1)
    @patch("store.views.api_client.listar_productos", return_value=[product])
    def test_catalog_offers_add_to_cart_to_visitors(self, list_products, count_products):
        response = self.client.get(reverse("catalogo"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Agregar al carrito")
        self.assertContains(response, reverse("carrito_agregar", args=["product-1"]))

    @patch("store.api_client.requests.request")
    def test_order_request_uses_bearer_token(self, request_api):
        response = request_api.return_value
        response.status_code = 201
        response.content = b"{}"
        response.json.return_value = {"id": "order-1"}

        api_client.crear_pedido(
            {"items": [{"producto_id": "product-1", "cantidad": 1}], "direccion_envio": "Calle 123"},
            "client-token",
        )

        self.assertEqual(
            request_api.call_args.kwargs["headers"]["Authorization"],
            "Bearer client-token",
        )
