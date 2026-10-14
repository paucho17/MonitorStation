"""Fabrica de endpoints CRUD con eliminacion logica.

A partir de la descripcion de un recurso (tabla, campos, modulo de
permisos) genera las rutas:

    GET     /api/<ruta>                 lista (filtros, paginacion)
    GET     /api/<ruta>/{id}            detalle
    POST    /api/<ruta>                 crea
    PUT     /api/<ruta>/{id}            actualiza parcialmente
    DELETE  /api/<ruta>/{id}            eliminacion logica (estado = FALSE)
    POST    /api/<ruta>/{id}/restaurar  reactiva (estado = TRUE)

Los campos "creado" y "actualizado" los administra el motor de base de
datos; el campo "estado" solo se modifica mediante DELETE y restaurar.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from psycopg import sql
from pydantic import Field, create_model

from app.db import get_db, traducir_error
from app.security import requerir_permiso


@dataclass
class Campo:
    """Describe una columna editable de un recurso."""

    nombre: str
    tipo: type
    requerido: bool = False
    max_len: Optional[int] = None
    min_len: Optional[int] = None
    editable: bool = True       # False: solo se puede definir al crear
    virtual: bool = False       # No es columna: lo procesa el hook y no se devuelve
    mayusculas: bool = False    # Normaliza el texto a mayusculas


@dataclass
class Recurso:
    """Descripcion declarativa de un recurso de la API."""

    ruta: str                       # /api/<ruta>
    tabla: str
    modulo: str                     # nombre en la tabla modulo (permisos)
    campos: list[Campo]
    filtros: list[str] = field(default_factory=list)
    permitir_crear: bool = True
    permitir_editar: bool = True
    orden_descendente: bool = False
    proteger_propio: bool = False   # Impide que un usuario se elimine a si mismo
    antes_guardar: Optional[Callable[[dict], dict]] = None

    @property
    def columnas(self) -> list[str]:
        """Columnas devueltas por la API."""
        propias = [c.nombre for c in self.campos if not c.virtual]
        return ["id", *propias, "estado", "creado", "actualizado"]


def _modelo(nombre: str, recurso: Recurso, crear: bool):
    """Genera el modelo Pydantic de entrada (creacion o actualizacion)."""
    definiciones: dict[str, Any] = {}
    for c in recurso.campos:
        if not crear and not c.editable:
            continue
        restricciones: dict[str, Any] = {}
        if c.max_len:
            restricciones["max_length"] = c.max_len
        if c.min_len:
            restricciones["min_length"] = c.min_len
        if crear and c.requerido:
            definiciones[c.nombre] = (c.tipo, Field(..., **restricciones))
        else:
            definiciones[c.nombre] = (Optional[c.tipo], Field(None, **restricciones))
    return create_model(nombre, **definiciones)


def _normalizar(recurso: Recurso, datos: dict) -> dict:
    """Aplica mayusculas, recorta espacios y ejecuta el hook del recurso."""
    for c in recurso.campos:
        valor = datos.get(c.nombre)
        if isinstance(valor, str):
            valor = valor.strip()
            if c.mayusculas:
                valor = valor.upper()
            datos[c.nombre] = valor
    if recurso.antes_guardar:
        datos = recurso.antes_guardar(datos)
    return datos


def crear_router(r: Recurso) -> APIRouter:
    """Construye el router del recurso."""
    router = APIRouter(prefix=f"/api/{r.ruta}", tags=[r.ruta])
    tabla = sql.Identifier(r.tabla)
    columnas = sql.SQL(", ").join(sql.Identifier(c) for c in r.columnas)
    sentido = sql.SQL("DESC" if r.orden_descendente else "ASC")
    modelo_crear = _modelo(f"{r.tabla}_crear", r, crear=True)
    modelo_editar = _modelo(f"{r.tabla}_editar", r, crear=False)

    def _obtener(db: psycopg.Connection, id_: int, solo_activos: bool = False) -> dict:
        consulta = sql.SQL("SELECT {c} FROM {t} WHERE id = %s").format(c=columnas, t=tabla)
        if solo_activos:
            consulta += sql.SQL(" AND estado = TRUE")
        fila = db.execute(consulta, (id_,)).fetchone()
        if fila is None:
            raise HTTPException(404, "Registro no encontrado")
        return fila

    # ----------------------------- LISTAR -----------------------------
    @router.get("", summary=f"Listar {r.ruta}")
    def listar(
        request: Request,
        incluir_inactivos: bool = Query(False, description="Incluye registros eliminados logicamente"),
        limite: int = Query(100, ge=1, le=500),
        desplazamiento: int = Query(0, ge=0),
        _=Depends(requerir_permiso(r.modulo, "leer")),
        db: psycopg.Connection = Depends(get_db),
    ):
        condiciones: list[sql.Composable] = []
        parametros: list[Any] = []
        if not incluir_inactivos:
            condiciones.append(sql.SQL("estado = TRUE"))
        for nombre in r.filtros:
            valor = request.query_params.get(nombre)
            if valor is not None:
                condiciones.append(sql.SQL("{} = %s").format(sql.Identifier(nombre)))
                parametros.append(valor)
        donde = sql.SQL(" WHERE ") + sql.SQL(" AND ").join(condiciones) if condiciones else sql.SQL("")
        try:
            total = db.execute(
                sql.SQL("SELECT count(*) AS n FROM {t}").format(t=tabla) + donde, parametros
            ).fetchone()["n"]
            filas = db.execute(
                sql.SQL("SELECT {c} FROM {t}").format(c=columnas, t=tabla)
                + donde
                + sql.SQL(" ORDER BY id {s} LIMIT %s OFFSET %s").format(s=sentido),
                [*parametros, limite, desplazamiento],
            ).fetchall()
        except psycopg.Error as exc:
            db.rollback()
            raise traducir_error(exc)
        return {"total": total, "limite": limite, "desplazamiento": desplazamiento, "datos": filas}

    # ----------------------------- DETALLE -----------------------------
    @router.get("/{id_}", summary=f"Detalle de {r.ruta}")
    def detalle(
        id_: int,
        _=Depends(requerir_permiso(r.modulo, "leer")),
        db: psycopg.Connection = Depends(get_db),
    ):
        return _obtener(db, id_)

    # ----------------------------- CREAR -----------------------------
    if r.permitir_crear:

        @router.post("", status_code=201, summary=f"Crear en {r.ruta}")
        def crear(
            datos: modelo_crear,  # type: ignore[valid-type]
            _=Depends(requerir_permiso(r.modulo, "crear")),
            db: psycopg.Connection = Depends(get_db),
        ):
            valores = _normalizar(r, datos.model_dump(exclude_unset=True))
            nombres = list(valores.keys())
            consulta = sql.SQL("INSERT INTO {t} ({n}) VALUES ({v}) RETURNING id").format(
                t=tabla,
                n=sql.SQL(", ").join(sql.Identifier(n) for n in nombres),
                v=sql.SQL(", ").join(sql.Placeholder() for _ in nombres),
            )
            try:
                nuevo_id = db.execute(consulta, list(valores.values())).fetchone()["id"]
                db.commit()
            except psycopg.Error as exc:
                db.rollback()
                raise traducir_error(exc)
            return _obtener(db, nuevo_id)

    # ----------------------------- ACTUALIZAR -----------------------------
    if r.permitir_editar:

        @router.put("/{id_}", summary=f"Actualizar en {r.ruta}")
        def actualizar(
            id_: int,
            datos: modelo_editar,  # type: ignore[valid-type]
            _=Depends(requerir_permiso(r.modulo, "editar")),
            db: psycopg.Connection = Depends(get_db),
        ):
            valores = _normalizar(r, datos.model_dump(exclude_unset=True))
            if not valores:
                raise HTTPException(400, "No se enviaron campos para actualizar")
            _obtener(db, id_)
            asignaciones = sql.SQL(", ").join(
                sql.SQL("{} = %s").format(sql.Identifier(n)) for n in valores
            )
            consulta = sql.SQL("UPDATE {t} SET {a} WHERE id = %s").format(t=tabla, a=asignaciones)
            try:
                db.execute(consulta, [*valores.values(), id_])
                db.commit()
            except psycopg.Error as exc:
                db.rollback()
                raise traducir_error(exc)
            return _obtener(db, id_)

    # ----------------------------- ELIMINAR (logico) -----------------------------
    @router.delete("/{id_}", summary=f"Eliminar (logico) en {r.ruta}")
    def eliminar(
        id_: int,
        usuario: dict = Depends(requerir_permiso(r.modulo, "eliminar")),
        db: psycopg.Connection = Depends(get_db),
    ):
        if r.proteger_propio and usuario["id"] == id_:
            raise HTTPException(400, "No puede eliminar su propio usuario")
        _obtener(db, id_)
        try:
            db.execute(sql.SQL("UPDATE {t} SET estado = FALSE WHERE id = %s").format(t=tabla), (id_,))
            db.commit()
        except psycopg.Error as exc:
            db.rollback()
            raise traducir_error(exc)
        return _obtener(db, id_)

    # ----------------------------- RESTAURAR -----------------------------
    @router.post("/{id_}/restaurar", summary=f"Restaurar en {r.ruta}")
    def restaurar(
        id_: int,
        _=Depends(requerir_permiso(r.modulo, "editar")),
        db: psycopg.Connection = Depends(get_db),
    ):
        _obtener(db, id_)
        try:
            db.execute(sql.SQL("UPDATE {t} SET estado = TRUE WHERE id = %s").format(t=tabla), (id_,))
            db.commit()
        except psycopg.Error as exc:
            db.rollback()
            raise traducir_error(exc)
        return _obtener(db, id_)

    return router
