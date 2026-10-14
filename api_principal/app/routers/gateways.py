"""Gateways LoRa: alta con clave de API y rotacion de la clave.

La clave se muestra una única vez (al crear o rotar); en la base de datos
solo se guarda su hash SHA-256. El listado, detalle, edicion, eliminacion
logica y restauracion usan el CRUD generico.
"""

from datetime import datetime
from typing import Optional

import psycopg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.crud import Campo, Recurso, crear_router
from app.db import get_db, traducir_error
from app.security import generar_clave_api, hash_clave_api, requerir_permiso

router = APIRouter()

# CRUD generico sin 'crear' (el alta genera la clave de API)
_recurso = Recurso(
    ruta="gateways", tabla="gateway", modulo="gateways",
    campos=[
        Campo("codigo", str, editable=False, mayusculas=True),
        Campo("nombre", str, max_len=100),
        Campo("zona_id", int),
        Campo("ultima_conexion", datetime, editable=False),
    ],
    filtros=["zona_id"], permitir_crear=False,
)


class GatewayIn(BaseModel):
    codigo: str = Field(min_length=1, max_length=20)
    nombre: str = Field(min_length=1, max_length=100)
    zona_id: Optional[int] = None


@router.post("/api/gateways", status_code=201, tags=["gateways"], summary="Crear gateway y generar su clave")
def crear_gateway(
    datos: GatewayIn,
    _=Depends(requerir_permiso("gateways", "crear")),
    db: psycopg.Connection = Depends(get_db),
):
    clave = generar_clave_api()
    try:
        fila = db.execute(
            """INSERT INTO gateway (codigo, nombre, zona_id, api_key_hash)
               VALUES (%s, %s, %s, %s) RETURNING id, codigo, nombre, zona_id""",
            (datos.codigo.strip().upper(), datos.nombre.strip(), datos.zona_id, hash_clave_api(clave)),
        ).fetchone()
        db.commit()
    except psycopg.Error as exc:
        db.rollback()
        raise traducir_error(exc)
    return {**fila, "api_key": clave, "aviso": "Guarde la clave: no se volvera a mostrar"}


@router.post("/api/gateways/{id_}/rotar-clave", tags=["gateways"], summary="Generar una nueva clave de API")
def rotar_clave(
    id_: int,
    _=Depends(requerir_permiso("gateways", "editar")),
    db: psycopg.Connection = Depends(get_db),
):
    clave = generar_clave_api()
    try:
        fila = db.execute(
            "UPDATE gateway SET api_key_hash = %s WHERE id = %s RETURNING id, codigo",
            (hash_clave_api(clave), id_),
        ).fetchone()
        db.commit()
    except psycopg.Error as exc:
        db.rollback()
        raise traducir_error(exc)
    if fila is None:
        raise HTTPException(404, "Gateway no encontrado")
    return {**fila, "api_key": clave, "aviso": "La clave anterior ya no es valida"}


# El CRUD generico se agrega despues de las rutas propias
router.include_router(crear_router(_recurso))
