from django.urls import path
from . import views

urlpatterns = [
    path("", views.catalogo, name="catalogo"),
    path("login/", views.login_view, name="login"),
    path("registro/", views.registro_view, name="registro"),
    path("logout/", views.logout_view, name="logout"),
    path("panel/", views.panel_admin, name="panel_admin"),
    path("panel/productos/nuevo/", views.producto_nuevo, name="producto_nuevo"),
    path("panel/productos/seleccionados/", views.productos_seleccionados, name="productos_seleccionados"),
    path("panel/productos/<str:producto_id>/editar/", views.producto_editar, name="producto_editar"),
    path("carrito/", views.carrito, name="carrito"),
    path("carrito/agregar/<str:producto_id>/", views.carrito_agregar, name="carrito_agregar"),
    path("carrito/actualizar/", views.carrito_actualizar, name="carrito_actualizar"),
    path("carrito/eliminar/<str:producto_id>/", views.carrito_eliminar, name="carrito_eliminar"),
    path("carrito/confirmar/", views.carrito_confirmar, name="carrito_confirmar"),
]