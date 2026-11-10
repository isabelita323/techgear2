from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pymongo.errors import PyMongoError

from app.database import pedidos_col, productos_col, usuarios_col
from app.models.pedido import EstadoPedido, PedidoCreate, PedidoEstadoUpdate, PedidoOut
from app.security import require_admin, usuario_actual
from app.utils import serializar, to_object_id

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


@router.post("/", response_model=PedidoOut, status_code=201)
def crear_pedido(pedido: PedidoCreate, usuario: dict = Depends(usuario_actual)):
    usuarios_col.update_one(
        {"_id": usuario["_id"]},
        {
            "$set": {
                "email": usuario["email"],
                "nombre": usuario["nombre"],
            }
        },
    )

    items_out, descontados, total = [], [], 0.0
    try:
        for item in pedido.items:
            oid = to_object_id(item.producto_id)
            # Descuento atómico: solo si hay stock suficiente
            prod = productos_col.find_one_and_update(
                {"_id": oid, "stock": {"$gte": item.cantidad}},
                {"$inc": {"stock": -item.cantidad}},
            )
            if prod is None:
                if not productos_col.find_one({"_id": oid}):
                    raise HTTPException(404, f"Producto {item.producto_id} no existe")
                raise HTTPException(409, f"Stock insuficiente para {item.producto_id}")
            descontados.append((oid, item.cantidad))
            total += prod["precio"] * item.cantidad
            items_out.append({
                "producto_id": item.producto_id,
                "cantidad": item.cantidad,
                "nombre": prod["nombre"],
                "precio_unitario": prod["precio"],
            })
    except (HTTPException, PyMongoError):
        for oid, cant in descontados:
            productos_col.update_one({"_id": oid}, {"$inc": {"stock": cant}})
        raise

    doc = {
        "usuario_id": str(usuario["_id"]),
        "usuario_email": usuario["email"],
        "items": items_out,
        "direccion_envio": pedido.direccion_envio,
        "total": round(total, 2),
        "estado": EstadoPedido.pendiente.value,
        "fecha": datetime.now(timezone.utc),
    }
    try:
        res = pedidos_col.insert_one(doc)
    except PyMongoError:
        for oid, quantity in descontados:
            productos_col.update_one({"_id": oid}, {"$inc": {"stock": quantity}})
        raise
    doc["_id"] = res.inserted_id
    return serializar(doc)


@router.get("/", response_model=List[PedidoOut])
def listar_pedidos(usuario: dict = Depends(usuario_actual)):
    """Devuelve únicamente el historial del usuario autenticado."""
    identity_filters = [
        {"usuario_id": str(usuario["_id"])},
        {"usuario_email": usuario["email"]},
    ]
    legacy_id = usuario.get("django_id")
    if isinstance(legacy_id, int):
        identity_filters.append({"usuario_id": legacy_id})
    docs = pedidos_col.find({"$or": identity_filters}).sort("fecha", -1)
    return [serializar(d) for d in docs]


@router.get("/admin/todos", response_model=List[PedidoOut],
            dependencies=[Depends(require_admin)])
def listar_todos():
    return [serializar(d) for d in pedidos_col.find().sort("fecha", -1)]


@router.get("/{pedido_id}", response_model=PedidoOut)
def obtener_pedido(pedido_id: str, usuario: dict = Depends(usuario_actual)):
    doc = pedidos_col.find_one({"_id": to_object_id(pedido_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    owns_order = (
        doc.get("usuario_id") == str(usuario["_id"])
        or doc.get("usuario_email") == usuario.get("email")
        or (
            isinstance(usuario.get("django_id"), int)
            and doc.get("usuario_id") == usuario["django_id"]
        )
    )
    if usuario.get("rol") != "administrador" and not owns_order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return serializar(doc)


@router.patch("/{pedido_id}/estado", response_model=PedidoOut,
              dependencies=[Depends(require_admin)])
def cambiar_estado(pedido_id: str, cambio: PedidoEstadoUpdate):
    doc = pedidos_col.find_one_and_update(
        {"_id": to_object_id(pedido_id)},
        {"$set": {"estado": cambio.estado.value}},
        return_document=True,
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return serializar(doc)