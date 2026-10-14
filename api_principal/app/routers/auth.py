"""Autenticación: registro, inicio y cierre de sesión, perfil."""

import logging
from typing import Optional

import psycopg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app import security
from app.db import get_db, traducir_error
from app.security import generar_hash, usuario_actual, verificar_clave

log = logging.getLogger("iotmangrove.auth")
router = APIRouter(prefix="/api/auth", tags=["auth"])

# Se asigna desde main.py
configuracion = None


class RegistroIn(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=72)
    email: Optional[str] = Field(default=None, max_length=100)
    nombre_completo: Optional[str] = Field(default=None, max_length=120)


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=72)


@router.post("/registro", status_code=201, summary="Registro público (rol consulta)")
def registro(datos: RegistroIn, db: psycopg.Connection = Depends(get_db)):
    """Crea un usuario con el rol de menor privilegio ("consulta")."""
    if not configuracion.permitir_registro:
        raise HTTPException(403, "El registro público esta deshabilitado")
    email = (datos.email or "").strip() or None
    if email and "@" not in email:
        raise HTTPException(400, "Correo electronico inválido")
    try:
        rol = db.execute("SELECT id FROM rol WHERE nombre = 'consulta' AND estado = TRUE").fetchone()
        if rol is None:
            raise HTTPException(500, "Rol 'consulta' no configurado")
        fila = db.execute(
            """INSERT INTO usuario (rol_id, username, email, nombre_completo, password_hash)
               VALUES (%s, %s, %s, %s, %s) RETURNING id""",
            (rol["id"], datos.username.strip(), email, datos.nombre_completo, generar_hash(datos.password)),
        ).fetchone()
        db.commit()
    except psycopg.Error as exc:
        db.rollback()
        raise traducir_error(exc)
    return {"success": True, "message": "Usuario registrado", "usuario_id": fila["id"]}


@router.post("/login", summary="Inicio de sesión (devuelve el JWT)")
def login(datos: LoginIn, db: psycopg.Connection = Depends(get_db)):
    usuario = db.execute(
        """SELECT u.id, u.username::text AS username, u.password_hash, r.nombre::text AS rol
           FROM usuario u JOIN rol r ON r.id = u.rol_id
           WHERE u.username = %s AND u.estado = TRUE AND r.estado = TRUE""",
        (datos.username.strip(),),
    ).fetchone()
    # Siempre se ejecuta bcrypt, exista o no el usuario
    if not verificar_clave(datos.password, usuario["password_hash"] if usuario else None):
        raise HTTPException(401, "Credenciales inválidas")
    token, segundos = security.emitir_token(db, usuario)
    db.commit()
    log.info("Inicio de sesión: %s", usuario["username"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": segundos,
        "usuario": {"id": usuario["id"], "username": usuario["username"], "rol": usuario["rol"]},
    }


@router.post("/logout", summary="Cierre de sesión (revoca el JWT)")
def logout(usuario: dict = Depends(usuario_actual), db: psycopg.Connection = Depends(get_db)):
    db.execute("UPDATE sesion_token SET revocado = TRUE WHERE jti = %s", (usuario["jti"],))
    db.commit()
    return {"success": True}


@router.get("/me", summary="Perfil y permisos del usuario autenticado")
def perfil(usuario: dict = Depends(usuario_actual), db: psycopg.Connection = Depends(get_db)):
    if usuario["rol"] == "admin":
        permisos = db.execute(
            """SELECT nombre::text AS modulo, TRUE AS puede_leer, TRUE AS puede_crear,
                      TRUE AS puede_editar, TRUE AS puede_eliminar
               FROM modulo WHERE estado = TRUE ORDER BY nombre"""
        ).fetchall()
    else:
        permisos = db.execute(
            """SELECT m.nombre::text AS modulo, mr.puede_leer, mr.puede_crear,
                      mr.puede_editar, mr.puede_eliminar
               FROM modulo_rol mr JOIN modulo m ON m.id = mr.modulo_id
               WHERE mr.rol_id = %s AND mr.estado = TRUE AND m.estado = TRUE
               ORDER BY m.nombre""",
            (usuario["rol_id"],),
        ).fetchall()
    return {
        "id": usuario["id"],
        "username": usuario["username"],
        "email": usuario["email"],
        "rol": usuario["rol"],
        "permisos": permisos,
    }
