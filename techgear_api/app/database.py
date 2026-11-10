import os
import logging
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

MONGO_URL = (
    os.getenv("MONGO_URI")
    or os.getenv("MONGODB_URI")
    or os.getenv("MONGO_URL")
)
if not MONGO_URL:
    raise RuntimeError("Configura MONGODB_URI (MongoDB Atlas en producción)")
if os.getenv("VERCEL") and urlparse(MONGO_URL).hostname in {"localhost", "127.0.0.1"}:
    raise RuntimeError("Vercel necesita una URI de MongoDB remota, no localhost")
DB_NAME = os.getenv("MONGODB_DB", "techgear")

client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
logger = logging.getLogger(__name__)

db = client[DB_NAME]
productos_col = db["productos"]
pedidos_col = db["pedidos"]
usuarios_col = db["usuarios"]


def verificar_conexion() -> bool:
    try:
        client.admin.command("ping")
        usuarios_col.create_index("email", unique=True)
        return True
    except PyMongoError as exc:
        logger.warning("No se pudo verificar o preparar MongoDB: %s", exc)
        return False