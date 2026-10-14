"""IoT-Mangrove: API principal (FastAPI + PostgreSQL).

Punto de entrada de la aplicacion. Registra los routers, inicializa la
base de datos y sirve el front-end estatico.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import security
from app.config import cargar
from app.crud import crear_router
from app.db import abrir_pool, cerrar_pool, get_db, obtener_pool
from app.recursos import RECURSOS
from app.routers import auth, datos, gateways, ingesta
from app.security import generar_hash, hash_clave_api

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("iotmangrove")

cfg = cargar()
security.configurar(cfg)
auth.configuracion = cfg

DIRECTORIO_ESTATICO = Path(__file__).resolve().parent.parent / "static"


def sembrar_datos_iniciales() -> None:
    """Crea el administrador y sincroniza la clave del gateway inicial.

    Ambos valores provienen de variables de entorno, por lo que ninguna
    credencial se almacena en el codigo ni en los scripts SQL.
    """
    with obtener_pool().connection() as db:
        rol = db.execute("SELECT id FROM rol WHERE nombre = 'admin'").fetchone()
        if rol is None:
            log.error("No existe el rol 'admin': ejecute db/principal/02_semillas.sql")
            return

        existe = db.execute(
            "SELECT 1 FROM usuario WHERE username = %s", (cfg.admin_usuario,)
        ).fetchone()
        if existe is None:
            db.execute(
                """INSERT INTO usuario (rol_id, username, email, nombre_completo, password_hash)
                   VALUES (%s, %s, %s, 'Administrador', %s)""",
                (rol["id"], cfg.admin_usuario, cfg.admin_email, generar_hash(cfg.admin_clave)),
            )
            log.info("Usuario administrador '%s' creado", cfg.admin_usuario)

        if cfg.gateway_clave:
            db.execute(
                """INSERT INTO gateway (codigo, nombre, api_key_hash)
                   VALUES (%s, 'Gateway principal', %s)
                   ON CONFLICT (codigo) DO UPDATE SET api_key_hash = EXCLUDED.api_key_hash""",
                (cfg.gateway_codigo, hash_clave_api(cfg.gateway_clave)),
            )
            log.info("Clave de API del gateway %s sincronizada", cfg.gateway_codigo)
        db.commit()


@asynccontextmanager
async def ciclo_de_vida(_app: FastAPI):
    abrir_pool(cfg)
    sembrar_datos_iniciales()
    log.info("API iniciada")
    yield
    cerrar_pool()


app = FastAPI(
    title="IoT-Mangrove API",
    description="Monitoreo telemetrico de manglares: nodos LoRa, gateway y backend en la nube.",
    version="2.0.0",
    lifespan=ciclo_de_vida,
)

if cfg.cors_origenes:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origenes,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/api/salud", tags=["sistema"], summary="Comprobacion de estado")
def salud(db=Depends(get_db)):
    db.execute("SELECT 1")
    return {"estado": "ok"}


app.include_router(auth.router)
app.include_router(ingesta.router)
app.include_router(datos.router)
app.include_router(gateways.router)
for recurso in RECURSOS:
    app.include_router(crear_router(recurso))

# El front-end se monta al final para no tapar las rutas /api/*
if DIRECTORIO_ESTATICO.is_dir():
    app.mount("/", StaticFiles(directory=DIRECTORIO_ESTATICO, html=True), name="static")
