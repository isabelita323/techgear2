import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from app.database import verificar_conexion
from app.routers import pedidos, productos, usuarios

for required_setting in ("API_KEY", "JWT_SECRET"):
    if not os.getenv(required_setting):
        raise RuntimeError(f"{required_setting} debe estar configurada")

@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Prepara el índice único de email al arrancar (no falla si Mongo está apagado)
    verificar_conexion()
    yield


app = FastAPI(
    lifespan=lifespan,
    title="TechGear API",
    description="API de catálogo, usuarios y pedidos de TechGear",
    version="1.0.0",
)

app.include_router(productos.router)
app.include_router(pedidos.router)
app.include_router(usuarios.router)


@app.get("/", tags=["Sistema"])
def raiz():
    return {"mensaje": "TechGear API", "docs": "/docs"}


@app.get("/health", tags=["Sistema"])
def health():
    if not verificar_conexion():
        raise HTTPException(status_code=503, detail="MongoDB no está disponible")
    return {"status": "ok", "mongodb": "conectado"}