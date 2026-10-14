"""Acceso a PostgreSQL mediante un pool de conexiones (psycopg 3)."""

import logging
from typing import Iterator, Optional

import psycopg
from fastapi import HTTPException
from psycopg import errors
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.config import Configuracion

log = logging.getLogger("iotmangrove.db")

_pool: Optional[ConnectionPool] = None


def abrir_pool(cfg: Configuracion) -> ConnectionPool:
    """Crea y abre el pool global de conexiones."""
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            conninfo="",
            kwargs={
                "host": cfg.db_host,
                "port": cfg.db_puerto,
                "dbname": cfg.db_nombre,
                "user": cfg.db_usuario,
                "password": cfg.db_clave,
                "sslmode": cfg.db_sslmode,
                "row_factory": dict_row,
            },
            min_size=1,
            max_size=cfg.db_pool_max,
            timeout=10.0,
            open=False,
        )
        # wait=True hace fallar el arranque si la base no responde
        _pool.open(wait=True, timeout=30.0)
    return _pool


def cerrar_pool() -> None:
    """Cierra el pool al apagar la aplicacion."""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


def obtener_pool() -> ConnectionPool:
    if _pool is None:
        raise RuntimeError("El pool de conexiones no esta inicializado")
    return _pool


def get_db() -> Iterator[psycopg.Connection]:
    """Dependencia de FastAPI: entrega una conexion y la devuelve al pool.

    Si la petición termina con una excepción se hace rollback; de lo
    contrario el pool confirma la transaccion al salir.
    """
    with obtener_pool().connection() as conn:
        yield conn


def traducir_error(exc: Exception) -> HTTPException:
    """Convierte errores de PostgreSQL en respuestas HTTP comprensibles."""
    if isinstance(exc, errors.UniqueViolation):
        restriccion = exc.diag.constraint_name or "único"
        return HTTPException(409, f"Ya existe un registro con ese valor ({restriccion})")
    if isinstance(exc, errors.ForeignKeyViolation):
        return HTTPException(400, "Referencia inválida: el registro relacionado no existe")
    if isinstance(exc, errors.NotNullViolation):
        return HTTPException(400, f"Campo obligatorio ausente: {exc.diag.column_name}")
    if isinstance(exc, (errors.CheckViolation, errors.DataError)):
        return HTTPException(400, "Valor fuera de rango o con formato inválido")
    log.exception("Error de base de datos no controlado")
    return HTTPException(500, "Error interno de base de datos")
