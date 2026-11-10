"""Carga datos iniciales en MongoDB: un administrador y 4 productos de ejemplo.

Uso (desde la carpeta techgear_api, con el entorno virtual activo):
    python seed.py --email admin@techgear.com
Te pedirá la contraseña (mínimo 6 caracteres). Es seguro ejecutarlo varias veces:
no duplica el administrador ni los productos.
"""
import argparse
import getpass
from datetime import datetime, timezone

import bcrypt

from app.database import productos_col, usuarios_col, verificar_conexion

PRODUCTOS = [
    {"nombre": "Labial rosa", "descripcion": "Labial cremoso de larga duración en tono rosa.",
     "precio": 35000, "stock": 25, "categoria": "Maquillaje",
     "imagen_url": "/media/productos/labial-rosa.jpg"},
    {"nombre": "Paleta de tonos", "descripcion": "Paleta de sombras con tonos cálidos y rosados.",
     "precio": 68000, "stock": 15, "categoria": "Maquillaje",
     "imagen_url": "/media/productos/paleta-tonos.jpg"},
    {"nombre": "Perfume floral", "descripcion": "Fragancia floral fresca para el día a día.",
     "precio": 120000, "stock": 10, "categoria": "Fragancias",
     "imagen_url": "/media/productos/perfume-floral.jpg"},
    {"nombre": "Sérum hidratante", "descripcion": "Sérum facial con ácido hialurónico para hidratar la piel.",
     "precio": 54000, "stock": 20, "categoria": "Cuidado de la piel",
     "imagen_url": "/media/productos/serum-hidratante.jpg"},
]


def main():
    parser = argparse.ArgumentParser(description="Datos iniciales de TechGear")
    parser.add_argument("--email", required=True, help="Email del administrador")
    parser.add_argument("--nombre", default="Administrador")
    args = parser.parse_args()

    if not verificar_conexion():
        raise SystemExit(
            "No se pudo conectar a MongoDB. Inicia el servicio de MongoDB "
            "o revisa MONGODB_URI en techgear_api/.env"
        )

    email = args.email.strip().lower()
    if usuarios_col.find_one({"email": email}):
        usuarios_col.update_one({"email": email}, {"$set": {"rol": "administrador"}})
        print(f"El usuario {email} ya existía: ahora es administrador.")
    else:
        password = getpass.getpass("Contraseña del administrador (6-72 caracteres): ")
        if not 6 <= len(password.encode()) <= 72:
            raise SystemExit("La contraseña debe tener entre 6 y 72 caracteres.")
        usuarios_col.insert_one({
            "nombre": args.nombre,
            "email": email,
            "password_hash": bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
            "rol": "administrador",
            "fecha_registro": datetime.now(timezone.utc),
        })
        print(f"Administrador creado: {email}")

    if productos_col.count_documents({}) == 0:
        productos_col.insert_many([dict(p) for p in PRODUCTOS])
        print(f"Se insertaron {len(PRODUCTOS)} productos de ejemplo.")
    else:
        print("Ya hay productos en la base de datos: no se insertó nada.")


if __name__ == "__main__":
    main()
