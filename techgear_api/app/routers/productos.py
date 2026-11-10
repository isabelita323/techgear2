from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response

from app.database import productos_col
from app.models.producto import ProductoCreate, ProductoOut, ProductoUpdate
from app.security import require_admin
from app.utils import serializar, to_object_id

router = APIRouter(prefix="/productos", tags=["Productos"])


@router.get("/", response_model=List[ProductoOut])
def listar_productos(
    categoria: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    filtro = {"categoria": categoria} if categoria else {}
    docs = productos_col.find(filtro).skip(skip).limit(limit)
    return [serializar(d) for d in docs]


@router.get("/count")
def contar_productos():
    return {"total": productos_col.count_documents({})}


@router.get("/{producto_id}", response_model=ProductoOut)
def obtener_producto(producto_id: str):
    doc = productos_col.find_one({"_id": to_object_id(producto_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return serializar(doc)


@router.post("/", response_model=ProductoOut, status_code=201,
             dependencies=[Depends(require_admin)])
def crear_producto(producto: ProductoCreate):
    data = producto.model_dump()
    res = productos_col.insert_one(data)
    data["_id"] = res.inserted_id
    return serializar(data)


@router.put("/{producto_id}", response_model=ProductoOut,
            dependencies=[Depends(require_admin)])
def actualizar_producto(producto_id: str, cambios: ProductoUpdate):
    datos = cambios.model_dump(exclude_unset=True)
    if not datos:
        raise HTTPException(status_code=400, detail="No se enviaron campos para actualizar")
    doc = productos_col.find_one_and_update(
        {"_id": to_object_id(producto_id)},
        {"$set": datos},
        return_document=True,
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return serializar(doc)


@router.delete("/{producto_id}", status_code=204,
               dependencies=[Depends(require_admin)])
def eliminar_producto(producto_id: str):
    res = productos_col.delete_one({"_id": to_object_id(producto_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return Response(status_code=204)