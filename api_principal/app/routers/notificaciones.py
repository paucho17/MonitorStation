"""Notificaciones: preferencias del usuario autenticado y envio de prueba.

La bitacora completa se consulta con el recurso CRUD /api/notificaciones
(solo lectura). Aqui se agregan:

  GET/PUT /api/notificaciones/preferencias : cada usuario ve y cambia sus avisos.
  POST    /api/notificaciones/prueba       : envia un correo de prueba al usuario.
"""

from typing import Literal

import psycopg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app import notificaciones
from app.db import get_db
from app.security import requerir_permiso, usuario_actual

router = APIRouter(prefix="/api/notificaciones", tags=["notificaciones"])


class PreferenciasIn(BaseModel):
    notificar_alertas: bool
    notificar_nivel: Literal["ADVERTENCIA", "CRITICO"] = "CRITICO"


@router.get("/preferencias", summary="Preferencias de aviso del usuario actual")
def ver_preferencias(usuario: dict = Depends(usuario_actual), db: psycopg.Connection = Depends(get_db)):
    fila = db.execute(
        "SELECT email::text AS email, notificar_alertas, notificar_nivel::text AS notificar_nivel FROM usuario WHERE id = %s",
        (usuario["id"],),
    ).fetchone()
    return fila


@router.put("/preferencias", summary="Cambiar las preferencias de aviso del usuario actual")
def cambiar_preferencias(
    datos: PreferenciasIn,
    usuario: dict = Depends(usuario_actual),
    db: psycopg.Connection = Depends(get_db),
):
    if datos.notificar_alertas and not usuario.get("email"):
        raise HTTPException(400, "Registre un correo en su perfil para recibir avisos")
    db.execute(
        "UPDATE usuario SET notificar_alertas = %s, notificar_nivel = %s WHERE id = %s",
        (datos.notificar_alertas, datos.notificar_nivel, usuario["id"]),
    )
    db.commit()
    return {"success": True, **datos.model_dump()}


@router.post("/prueba", summary="Enviar un correo de prueba al usuario actual")
def prueba(
    usuario: dict = Depends(requerir_permiso("notificaciones", "crear")),
):
    if not usuario.get("email"):
        raise HTTPException(400, "Su usuario no tiene correo registrado")
    try:
        notificaciones.enviar_prueba(usuario["email"])
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"No se pudo enviar: {exc}")
    return {"success": True, "destino": usuario["email"]}
