from datetime import datetime, timezone

import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from pymongo.errors import DuplicateKeyError

from app.database import usuarios_col
from app.models.usuarios import (
    Rol, TokenOut, UsuarioLogin, UsuarioOut, UsuarioRegistro,
)
from app.security import crear_token, usuario_actual
from app.utils import serializar

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


def _publico(doc: dict) -> dict:
    doc = dict(doc)
    doc.pop("password_hash", None)
    return serializar(doc)


@router.post("/registro", response_model=UsuarioOut, status_code=201)
def registro(datos: UsuarioRegistro):
    doc = {
        "nombre": datos.nombre,
        "email": datos.email.lower(),
        "password_hash": bcrypt.hashpw(
            datos.password.encode(), bcrypt.gensalt()
        ).decode(),
        "rol": Rol.cliente.value,   # nadie se registra como admin
        "fecha_registro": datetime.now(timezone.utc),
    }
    try:
        res = usuarios_col.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Ya existe un usuario con ese email")
    doc["_id"] = res.inserted_id
    return _publico(doc)


@router.post("/login", response_model=TokenOut)
def login(datos: UsuarioLogin):
    doc = usuarios_col.find_one({"email": datos.email.lower()})
    if not doc or "password_hash" not in doc or not bcrypt.checkpw(
        datos.password.encode(), doc["password_hash"].encode()
    ):
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")
    token = crear_token(str(doc["_id"]), doc["rol"])
    return {"access_token": token, "token_type": "bearer", "usuario": _publico(doc)}


@router.get("/me", response_model=UsuarioOut)
def perfil(usuario: dict = Depends(usuario_actual)):
    return _publico(usuario)