import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from bson import ObjectId
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from app.database import usuarios_col

# ---- API key (administración desde servidor) ----
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_admin(key: str = Security(api_key_header)):
    esperada = os.getenv("API_KEY", "")
    if not key or not esperada or not secrets.compare_digest(key, esperada):
        raise HTTPException(status_code=401, detail="API key inválida o ausente")


# ---- JWT (usuarios) ----
ALGORITMO = "HS256"
bearer = HTTPBearer(auto_error=False)


def _secreto() -> str:
    s = os.getenv("JWT_SECRET")
    if not s:
        raise HTTPException(status_code=500, detail="JWT_SECRET no configurado")
    return s


def crear_token(usuario_id: str, rol: str) -> str:
    minutos = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
    payload = {
        "sub": usuario_id,
        "rol": rol,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=minutos),
    }
    return jwt.encode(payload, _secreto(), algorithm=ALGORITMO)


def usuario_actual(cred: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    if cred is None:
        raise HTTPException(status_code=401, detail="Token ausente")
    try:
        payload = jwt.decode(cred.credentials, _secreto(), algorithms=[ALGORITMO])
        doc = usuarios_col.find_one({"_id": ObjectId(payload["sub"])})
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")
    if not doc:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return doc


def solo_admin(usuario: dict = Depends(usuario_actual)) -> dict:
    if usuario.get("rol") != "administrador":
        raise HTTPException(status_code=403, detail="Se requiere rol administrador")
    return usuario