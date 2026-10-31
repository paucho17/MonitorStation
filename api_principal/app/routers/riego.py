"""Sistema de riego: estado, modos de operacion, mando manual y enlace con el controlador central.

Hay dos audiencias:

  * Panel web (JWT, modulo "riego"): consulta el estado, cambia el modo de
    cada zona y envia ordenes manuales de abrir o cerrar.
  * Controlador central (cabecera X-API-Key): descarga la configuracion y las
    ordenes pendientes, y reporta posiciones, resultados y riegos hechos.

Las ordenes se guardan en una cola (comando_riego). El panel nunca activa un
actuador directamente: el controlador central las ejecuta y confirma, y es
quien aplica en sitio los enclavamientos de seguridad (tiempo maximo, descanso,
limite diario y nivel del tanque).
"""

import logging
from datetime import datetime, timezone
from typing import Literal, Optional

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.db import get_db, traducir_error
from app.security import gateway_autenticado, requerir_permiso

log = logging.getLogger("iotmangrove.riego")
router = APIRouter(prefix="/api/riego", tags=["riego"])

MODOS = ("AUTO", "PROGRAMADO", "MANUAL", "APAGADO")
# Una orden que no se entrega en este tiempo se cancela, para no abrir una valvula tarde
MINUTOS_CADUCIDAD_ORDEN = 10
# Duracion maxima de una orden sobre un actuador sin zona (bomba)
DURACION_MAX_SIN_ZONA_S = 3600


class ModoIn(BaseModel):
    modo: Literal["AUTO", "PROGRAMADO", "MANUAL", "APAGADO"]


class ComandoIn(BaseModel):
    actuador_id: int
    accion: Literal["ABRIR", "CERRAR"]
    duracion_s: Optional[int] = Field(default=None, gt=0, le=86400)


class ComandoResultadoIn(BaseModel):
    id: int
    situacion: Literal["EJECUTADO", "FALLIDO"]
    detalle: Optional[str] = Field(default=None, max_length=255)


class ActuadorReporteIn(BaseModel):
    codigo: str = Field(min_length=1, max_length=20)
    posicion: Literal["ABIERTA", "CERRADA", "ENCENDIDA", "APAGADA", "DESCONOCIDA"]


class EventoIn(BaseModel):
    actuador: str = Field(min_length=1, max_length=20)
    inicio: datetime
    fin: Optional[datetime] = None
    duracion_s: Optional[int] = Field(default=None, ge=0)
    origen: Literal["MANUAL", "AUTO", "PROGRAMADO", "SEGURIDAD"] = "AUTO"
    motivo: Optional[str] = Field(default=None, max_length=255)


class ReporteIn(BaseModel):
    actuadores: list[ActuadorReporteIn] = Field(default_factory=list)
    comandos: list[ComandoResultadoIn] = Field(default_factory=list)
    eventos: list[EventoIn] = Field(default_factory=list)


def _segundos_hoy(db: psycopg.Connection, zona_id: int) -> int:
    """Segundos regados hoy (dia UTC) en una zona, segun la bitacora."""
    fila = db.execute(
        """SELECT COALESCE(sum(duracion_s), 0)::int AS s FROM evento_riego
           WHERE zona_riego_id = %s AND estado = TRUE
             AND inicio >= date_trunc('day', now())""",
        (zona_id,),
    ).fetchone()
    return fila["s"]


def _zona_de(db: psycopg.Connection, zona_id: int) -> dict:
    zona = db.execute("SELECT * FROM zona_riego WHERE id = %s AND estado = TRUE", (zona_id,)).fetchone()
    if zona is None:
        raise HTTPException(404, "Zona de riego no encontrada")
    return zona


# ============================== PANEL WEB ==============================

@router.get("/estado", summary="Estado de las zonas, actuadores y ultimos riegos")
def estado(
    ambito: Optional[str] = Query(None, description="Filtra zonas por ambito, p. ej. VIVERO"),
    _=Depends(requerir_permiso("riego", "leer")),
    db: psycopg.Connection = Depends(get_db),
):
    codigos = [c.strip().upper() for c in (ambito or "").split(",") if c.strip() and c.strip().upper() != "TODOS"]
    zonas = db.execute(
        """
        SELECT z.id, z.codigo, z.nombre, z.modo, a.codigo AS ambito,
               z.humedad_min, z.humedad_max, z.duracion_max_s, z.descanso_min_s, z.limite_diario_s,
               n.codigo AS nodo_sensor, v.codigo AS variable,
               (SELECT m.valor FROM medicion m JOIN lectura l ON l.id = m.lectura_id
                 WHERE l.nodo_id = z.nodo_sensor_id AND m.variable_id = z.variable_id
                   AND m.estado = TRUE AND l.estado = TRUE
                 ORDER BY l.fecha_recepcion DESC LIMIT 1) AS humedad_actual,
               (SELECT l.fecha_recepcion FROM medicion m JOIN lectura l ON l.id = m.lectura_id
                 WHERE l.nodo_id = z.nodo_sensor_id AND m.variable_id = z.variable_id
                   AND m.estado = TRUE AND l.estado = TRUE
                 ORDER BY l.fecha_recepcion DESC LIMIT 1) AS humedad_fecha,
               (SELECT COALESCE(sum(e.duracion_s), 0)::int FROM evento_riego e
                 WHERE e.zona_riego_id = z.id AND e.estado = TRUE
                   AND e.inicio >= date_trunc('day', now())) AS regado_hoy_s
        FROM zona_riego z
        JOIN ambito a ON a.id = z.ambito_id
        LEFT JOIN nodo n ON n.id = z.nodo_sensor_id
        LEFT JOIN variable v ON v.id = z.variable_id
        WHERE z.estado = TRUE AND (%s::text[] = '{}' OR a.codigo = ANY(%s))
        ORDER BY z.id
        """,
        (codigos, codigos),
    ).fetchall()
    actuadores = db.execute(
        """SELECT id, codigo, nombre, tipo, zona_riego_id, posicion, ultimo_reporte
           FROM actuador WHERE estado = TRUE ORDER BY id"""
    ).fetchall()
    for z in zonas:
        z["actuadores"] = [a for a in actuadores if a["zona_riego_id"] == z["id"]]
    sueltos = [a for a in actuadores if a["zona_riego_id"] is None]
    eventos = db.execute(
        """SELECT e.id, a.codigo AS actuador, z.codigo AS zona, e.inicio, e.fin,
                  e.duracion_s, e.origen, e.motivo
           FROM evento_riego e JOIN actuador a ON a.id = e.actuador_id
           LEFT JOIN zona_riego z ON z.id = e.zona_riego_id
           WHERE e.estado = TRUE ORDER BY e.inicio DESC LIMIT 10"""
    ).fetchall()
    pendientes = db.execute(
        "SELECT count(*) AS n FROM comando_riego WHERE estado = TRUE AND situacion IN ('PENDIENTE','ENVIADO')"
    ).fetchone()["n"]
    return {
        "zonas": zonas,
        "actuadores_sin_zona": sueltos,
        "ultimos_eventos": eventos,
        "comandos_en_curso": pendientes,
        "modos": list(MODOS),
    }


@router.put("/zonas/{zona_id}/modo", summary="Cambiar el modo de operacion de una zona")
def cambiar_modo(
    zona_id: int,
    datos: ModoIn,
    usuario: dict = Depends(requerir_permiso("riego", "editar")),
    db: psycopg.Connection = Depends(get_db),
):
    """Al pasar a APAGADO se ordena cerrar las valvulas de la zona. Al salir
    de MANUAL se cancelan las ordenes manuales que aun no se entregaron."""
    zona = _zona_de(db, zona_id)
    try:
        db.execute("UPDATE zona_riego SET modo = %s WHERE id = %s", (datos.modo, zona_id))
        if datos.modo != "MANUAL":
            db.execute(
                """UPDATE comando_riego SET situacion = 'CANCELADO', detalle = 'cambio de modo'
                   WHERE situacion = 'PENDIENTE' AND origen = 'MANUAL' AND accion = 'ABRIR'
                     AND actuador_id IN (SELECT id FROM actuador WHERE zona_riego_id = %s)""",
                (zona_id,),
            )
        if datos.modo == "APAGADO":
            db.execute(
                """INSERT INTO comando_riego (actuador_id, accion, origen, usuario_id, detalle)
                   SELECT id, 'CERRAR', 'SEGURIDAD', %s, 'zona apagada'
                   FROM actuador WHERE zona_riego_id = %s AND tipo = 'VALVULA' AND estado = TRUE""",
                (usuario["id"], zona_id),
            )
        db.commit()
    except psycopg.Error as exc:
        db.rollback()
        raise traducir_error(exc)
    log.info("Zona %s: modo %s -> %s (%s)", zona["codigo"], zona["modo"], datos.modo, usuario["username"])
    return {"success": True, "zona": zona["codigo"], "modo": datos.modo}


@router.post("/comandos", status_code=201, summary="Orden manual de abrir o cerrar un actuador")
def crear_comando(
    datos: ComandoIn,
    usuario: dict = Depends(requerir_permiso("riego", "crear")),
    db: psycopg.Connection = Depends(get_db),
):
    """Cerrar siempre se acepta. Abrir exige que la zona este en MANUAL y que
    respete duracion maxima, descanso y limite diario (el controlador vuelve a
    comprobarlo en sitio)."""
    actuador = db.execute(
        "SELECT id, codigo, tipo, zona_riego_id FROM actuador WHERE id = %s AND estado = TRUE",
        (datos.actuador_id,),
    ).fetchone()
    if actuador is None:
        raise HTTPException(404, "Actuador no encontrado")

    duracion = datos.duracion_s
    if datos.accion == "ABRIR":
        if actuador["zona_riego_id"] is None:
            tope = DURACION_MAX_SIN_ZONA_S
            duracion = duracion or 600
        else:
            zona = _zona_de(db, actuador["zona_riego_id"])
            if zona["modo"] != "MANUAL":
                raise HTTPException(409, f"La zona {zona['codigo']} esta en modo {zona['modo']}: use MANUAL para abrir a mano")
            tope = zona["duracion_max_s"]
            duracion = duracion or tope
            if duracion > tope:
                raise HTTPException(400, f"La duracion maxima permitida es {tope} s")
            hoy = _segundos_hoy(db, zona["id"])
            if hoy + duracion > zona["limite_diario_s"]:
                raise HTTPException(409, f"Superaria el limite diario ({hoy} s ya regados de {zona['limite_diario_s']} s)")
            ultimo = db.execute(
                """SELECT EXTRACT(EPOCH FROM (now() - COALESCE(fin, inicio)))::int AS pasado
                   FROM evento_riego WHERE zona_riego_id = %s AND estado = TRUE
                   ORDER BY inicio DESC LIMIT 1""",
                (zona["id"],),
            ).fetchone()
            if ultimo and ultimo["pasado"] < zona["descanso_min_s"]:
                raise HTTPException(409, f"Zona en descanso: faltan {zona['descanso_min_s'] - ultimo['pasado']} s")
        if duracion > tope:
            raise HTTPException(400, f"La duracion maxima permitida es {tope} s")
    else:
        duracion = None

    try:
        fila = db.execute(
            """INSERT INTO comando_riego (actuador_id, accion, duracion_s, origen, usuario_id)
               VALUES (%s, %s, %s, 'MANUAL', %s) RETURNING id, situacion, creado""",
            (actuador["id"], datos.accion, duracion, usuario["id"]),
        ).fetchone()
        db.commit()
    except psycopg.Error as exc:
        db.rollback()
        raise traducir_error(exc)
    return {"success": True, "actuador": actuador["codigo"], "accion": datos.accion,
            "duracion_s": duracion, **fila}


@router.get("/comandos/{comando_id}", summary="Seguimiento de una orden")
def ver_comando(
    comando_id: int,
    _=Depends(requerir_permiso("riego", "leer")),
    db: psycopg.Connection = Depends(get_db),
):
    fila = db.execute(
        """SELECT c.id, a.codigo AS actuador, c.accion, c.duracion_s, c.origen,
                  c.situacion, c.detalle, c.creado, c.actualizado
           FROM comando_riego c JOIN actuador a ON a.id = c.actuador_id WHERE c.id = %s""",
        (comando_id,),
    ).fetchone()
    if fila is None:
        raise HTTPException(404, "Orden no encontrada")
    return fila


# ============================== CONTROLADOR CENTRAL ==============================

@router.get("/central/pendientes", summary="El controlador descarga configuracion y ordenes (X-API-Key)")
def central_pendientes(
    gateway: dict = Depends(gateway_autenticado),
    db: psycopg.Connection = Depends(get_db),
):
    """Entrega las zonas con sus reglas y programas, y las ordenes pendientes
    (que pasan a ENVIADO). Las ordenes viejas se cancelan en vez de entregarse."""
    try:
        db.execute(
            """UPDATE comando_riego SET situacion = 'CANCELADO', detalle = 'caducada'
               WHERE situacion = 'PENDIENTE' AND creado < now() - make_interval(mins => %s)""",
            (MINUTOS_CADUCIDAD_ORDEN,),
        )
        comandos = db.execute(
            """UPDATE comando_riego c SET situacion = 'ENVIADO'
               FROM actuador a
               WHERE c.actuador_id = a.id AND c.situacion = 'PENDIENTE' AND c.estado = TRUE
               RETURNING c.id, a.codigo AS actuador, c.accion, c.duracion_s, c.origen"""
        ).fetchall()
        db.execute("UPDATE gateway SET ultima_conexion = now() WHERE id = %s", (gateway["id"],))
        db.commit()
    except psycopg.Error as exc:
        db.rollback()
        raise traducir_error(exc)

    zonas = db.execute(
        """SELECT z.id, z.codigo, z.modo, z.humedad_min, z.humedad_max, z.duracion_max_s,
                  z.descanso_min_s, z.limite_diario_s, n.codigo AS nodo_sensor
           FROM zona_riego z LEFT JOIN nodo n ON n.id = z.nodo_sensor_id
           WHERE z.estado = TRUE ORDER BY z.id"""
    ).fetchall()
    actuadores = db.execute(
        "SELECT codigo, tipo, zona_riego_id FROM actuador WHERE estado = TRUE ORDER BY id"
    ).fetchall()
    programas = db.execute(
        """SELECT zona_riego_id, to_char(hora_inicio, 'HH24:MI') AS hora, duracion_s, dias
           FROM programa_riego WHERE estado = TRUE AND habilitado = TRUE ORDER BY zona_riego_id, hora_inicio"""
    ).fetchall()
    for z in zonas:
        z["valvulas"] = [a["codigo"] for a in actuadores if a["zona_riego_id"] == z["id"] and a["tipo"] == "VALVULA"]
        z["programas"] = [
            {"hora": p["hora"], "duracion_s": p["duracion_s"], "dias": p["dias"]}
            for p in programas if p["zona_riego_id"] == z["id"]
        ]
    return {
        "hora_servidor": datetime.now(timezone.utc).isoformat(),
        "zonas": zonas,
        "comandos": comandos,
    }


@router.post("/central/reporte", summary="El controlador reporta posiciones, resultados y riegos (X-API-Key)")
def central_reporte(
    reporte: ReporteIn,
    gateway: dict = Depends(gateway_autenticado),
    db: psycopg.Connection = Depends(get_db),
):
    ignorados: list[str] = []
    try:
        mapa = {
            a["codigo"]: a
            for a in db.execute("SELECT id, codigo, zona_riego_id FROM actuador WHERE estado = TRUE").fetchall()
        }
        for item in reporte.actuadores:
            codigo = item.codigo.strip().upper()
            if codigo not in mapa:
                ignorados.append(codigo)
                continue
            db.execute(
                "UPDATE actuador SET posicion = %s, ultimo_reporte = now() WHERE id = %s",
                (item.posicion, mapa[codigo]["id"]),
            )
        for c in reporte.comandos:
            db.execute(
                """UPDATE comando_riego SET situacion = %s, detalle = %s
                   WHERE id = %s AND situacion IN ('PENDIENTE', 'ENVIADO')""",
                (c.situacion, c.detalle, c.id),
            )
        eventos = 0
        for e in reporte.eventos:
            codigo = e.actuador.strip().upper()
            if codigo not in mapa:
                ignorados.append(codigo)
                continue
            duracion = e.duracion_s
            if duracion is None and e.fin is not None:
                duracion = max(0, int((e.fin - e.inicio).total_seconds()))
            db.execute(
                """INSERT INTO evento_riego (actuador_id, zona_riego_id, inicio, fin, duracion_s, origen, motivo)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (mapa[codigo]["id"], mapa[codigo]["zona_riego_id"], e.inicio, e.fin, duracion, e.origen, e.motivo),
            )
            eventos += 1
        db.execute("UPDATE gateway SET ultima_conexion = now() WHERE id = %s", (gateway["id"],))
        db.commit()
    except psycopg.Error as exc:
        db.rollback()
        raise traducir_error(exc)
    return {"success": True, "eventos_guardados": eventos, "ignorados": ignorados}
