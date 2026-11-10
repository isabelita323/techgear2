from datetime import datetime
from enum import Enum
from typing import List, Union
from pydantic import BaseModel, Field


class EstadoPedido(str, Enum):
    pendiente = "pendiente"
    enviado = "enviado"
    entregado = "entregado"
    cancelado = "cancelado"


class ItemPedido(BaseModel):
    producto_id: str
    cantidad: int = Field(..., gt=0)


class ItemPedidoOut(ItemPedido):
    nombre: str
    precio_unitario: float


class PedidoCreate(BaseModel):
    items: List[ItemPedido] = Field(..., min_length=1)
    direccion_envio: str = Field(..., min_length=5)


class PedidoEstadoUpdate(BaseModel):
    estado: EstadoPedido


class PedidoOut(BaseModel):
    id: str
    usuario_id: Union[int, str]
    items: List[ItemPedidoOut]
    direccion_envio: str
    total: float
    estado: EstadoPedido
    fecha: datetime
