"""Consulta de datos: ultimo estado (dashboard) e historial con filtros."""

from datetime import datetime
from typing import Optional

import psycopg
from fastapi import APIRouter, Depends, Query

from app.db import get_db
from app.security import requerir_permiso

router = APIRouter(prefix="/api", tags=["datos"])


@router.get("/dashboard", summary="Ultimo valor de cada variable por nodo")
def dashboard(
    _=Depends(requerir_permiso("dashboard", "leer")),
    db: psycopg.Connection = Depends(get_db),
):
    """Devuelve la ultima medicion de cada variable en cada nodo, la ultima
    lectura recibida, la ultima posicion GPS conocida y el numero de
    alertas pendientes."""
    variables = db.execute(
        """
        SELECT DISTINCT ON (m.variable_id, l.nodo_id)
               v.codigo AS variable, v.nombre AS variable_nombre, um.simbolo AS unidad,
               m.valor, n.codigo AS nodo, n.nombre AS nodo_nombre,
               l.fecha_recepcion, l.rssi, l.snr,
               (SELECT u.nivel FROM alerta a JOIN umbral u ON u.id = a.umbral_id
                 WHERE a.medicion_id = m.id AND a.estado = TRUE LIMIT 1) AS alerta_nivel
        FROM medicion m
        JOIN lectura l       ON l.id = m.lectura_id
        JOIN variable v      ON v.id = m.variable_id
        JOIN unidad_medida um ON um.id = v.unidad_id
        JOIN nodo n          ON n.id = l.nodo_id
        WHERE m.estado = TRUE AND l.estado = TRUE AND n.estado = TRUE AND v.estado = TRUE
        ORDER BY m.variable_id, l.nodo_id, l.fecha_recepcion DESC
        """
    ).fetchall()

    ultima = db.execute(
        """SELECT l.id, n.codigo AS nodo, g.codigo AS gateway, l.rssi, l.snr, l.fecha_recepcion
           FROM lectura l JOIN nodo n ON n.id = l.nodo_id JOIN gateway g ON g.id = l.gateway_id
           WHERE l.estado = TRUE ORDER BY l.fecha_recepcion DESC LIMIT 1"""
    ).fetchone()

    posicion = db.execute(
        """SELECT n.codigo AS nodo, l.latitud, l.longitud, l.satelites, l.fecha_recepcion
           FROM lectura l JOIN nodo n ON n.id = l.nodo_id
           WHERE l.estado = TRUE AND l.latitud IS NOT NULL AND l.longitud IS NOT NULL
           ORDER BY l.fecha_recepcion DESC LIMIT 1"""
    ).fetchone()

    pendientes = db.execute(
        "SELECT count(*) AS n FROM alerta WHERE estado = TRUE AND atendida = FALSE"
    ).fetchone()["n"]

    return {
        "ultima_lectura": ultima,
        "ultima_posicion": posicion,
        "alertas_pendientes": pendientes,
        "variables": variables,
    }


@router.get("/historial", summary="Historial de mediciones con filtros")
def historial(
    nodo: Optional[str] = Query(None, description="Codigo del nodo, p. ej. 0xAA"),
    variable: Optional[str] = Query(None, description="Codigo de la variable, p. ej. ph"),
    desde: Optional[datetime] = Query(None),
    hasta: Optional[datetime] = Query(None),
    limite: int = Query(200, ge=1, le=2000),
    desplazamiento: int = Query(0, ge=0),
    _=Depends(requerir_permiso("historial", "leer")),
    db: psycopg.Connection = Depends(get_db),
):
    condiciones = ["m.estado = TRUE", "l.estado = TRUE"]
    parametros: list = []
    if nodo:
        condiciones.append("n.codigo = %s")
        parametros.append(nodo.strip().upper())
    if variable:
        condiciones.append("v.codigo = %s")
        parametros.append(variable.strip().lower())
    if desde:
        condiciones.append("l.fecha_recepcion >= %s")
        parametros.append(desde)
    if hasta:
        condiciones.append("l.fecha_recepcion <= %s")
        parametros.append(hasta)
    donde = " AND ".join(condiciones)

    base = f"""
        FROM medicion m
        JOIN lectura l        ON l.id = m.lectura_id
        JOIN variable v       ON v.id = m.variable_id
        JOIN unidad_medida um ON um.id = v.unidad_id
        JOIN nodo n           ON n.id = l.nodo_id
        WHERE {donde}
    """
    total = db.execute(f"SELECT count(*) AS n {base}", parametros).fetchone()["n"]
    filas = db.execute(
        f"""SELECT m.id, l.fecha_recepcion, n.codigo AS nodo, v.codigo AS variable,
                   v.nombre AS variable_nombre, m.valor, um.simbolo AS unidad,
                   l.rssi, l.snr, l.latitud, l.longitud
            {base}
            ORDER BY l.fecha_recepcion DESC, m.id DESC
            LIMIT %s OFFSET %s""",
        [*parametros, limite, desplazamiento],
    ).fetchall()
    return {"total": total, "limite": limite, "desplazamiento": desplazamiento, "datos": filas}
