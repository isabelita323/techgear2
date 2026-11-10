from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr, Field


class Rol(str, Enum):
    cliente = "cliente"
    administrador = "administrador"


class UsuarioDB(BaseModel):
    """Esquema del documento en la colección 'usuarios' de Mongo."""
    nombre: str
    email: EmailStr
    password_hash: str
    rol: Rol = Rol.cliente
    fecha_registro: datetime


class UsuarioRegistro(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72)


class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str


class UsuarioOut(BaseModel):
    id: str
    nombre: str
    email: EmailStr
    rol: Rol
    fecha_registro: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut