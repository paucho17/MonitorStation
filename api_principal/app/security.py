"""Seguridad: hash de contraseñas, JWT, sesiones revocables y permisos.

Flujo:
  1. /api/auth/login valida usuario y contraseña (bcrypt) y emite un JWT
     firmado con HS256 que contiene sub, username, rol, jti, iat y exp.
  2. Cada JWT se registra en la tabla sesion_token (por su jti). Asi el
     cierre de sesión puede revocarlo antes de que expire.
  3. Cada petición protegida valida firma, expiracion y que el jti siga
     vigente; luego se verifica el permiso del rol sobre el modulo en la
     tabla modulo_rol.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Callable

import bcrypt
import jwt
import psycopg
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from psycopg import sql

from app.db import get_db

# La configuracion se inyecta desde main.py al iniciar
_cfg = None

ACCIONES = {
    "leer": "puede_leer",
    "crear": "puede_crear",
    "editar": "puede_editar",
    "eliminar": "puede_eliminar",
}

_esquema_bearer = HTTPBearer(auto_error=False, description="JWT obtenido en /api/auth/login")

# Hash ficticio para igualar tiempos cuando el usuario no existe
_HASH_FALSO = bcrypt.hashpw(b"contrasena-ficticia", bcrypt.gensalt()).decode()


def configurar(cfg) -> None:
    """Registra la configuracion global del modulo."""
    global _cfg
    _cfg = cfg


# ----------------------------- Contraseñas -----------------------------
def validar_longitud_clave(clave: str) -> None:
    """bcrypt solo procesa 72 bytes; se rechazan claves mas largas."""
    if len(clave.encode("utf-8")) > 72:
        raise HTTPException(400, "La contraseña no puede superar 72 bytes")


def generar_hash(clave: str) -> str:
    validar_longitud_clave(clave)
    return bcrypt.hashpw(clave.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_clave(clave: str, hash_guardado: str | None) -> bool:
    """Compara en tiempo constante; devuelve False ante cualquier error."""
    objetivo = hash_guardado or _HASH_FALSO
    try:
        valido = bcrypt.checkpw(clave.encode("utf-8"), objetivo.encode("utf-8"))
    except ValueError:
        return False
    return valido and hash_guardado is not None


# ----------------------------- Claves de gateway -----------------------------
def generar_clave_api() -> str:
    """Genera una clave aleatoria para un gateway."""
    return secrets.token_urlsafe(32)


def hash_clave_api(clave: str) -> str:
    """SHA-256 hexadecimal (la clave es aleatoria de alta entropia)."""
    return hashlib.sha256(clave.encode("utf-8")).hexdigest()


# ----------------------------- JWT -----------------------------
def emitir_token(db: psycopg.Connection, usuario: dict) -> tuple[str, int]:
    """Crea un JWT, lo registra en sesion_token y devuelve (token, segundos)."""
    ahora = datetime.now(timezone.utc)
    expira = ahora + timedelta(minutes=_cfg.jwt_minutos)
    jti = uuid.uuid4().hex
    carga = {
        "sub": str(usuario["id"]),
        "username": usuario["username"],
        "rol": usuario["rol"],
        "jti": jti,
        "iat": ahora,
        "exp": expira,
    }
    token = jwt.encode(carga, _cfg.jwt_secreto, algorithm=_cfg.jwt_algoritmo)
    db.execute(
        "INSERT INTO sesion_token (usuario_id, jti, expira_en) VALUES (%s, %s, %s)",
        (usuario["id"], jti, expira),
    )
    return token, _cfg.jwt_minutos * 60


def usuario_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(_esquema_bearer),
    db: psycopg.Connection = Depends(get_db),
) -> dict:
    """Valida el JWT y devuelve el usuario autenticado."""
    cabecera = {"WWW-Authenticate": "Bearer"}
    if credenciales is None:
        raise HTTPException(401, "Token requerido", headers=cabecera)
    try:
        carga = jwt.decode(
            credenciales.credentials,
            _cfg.jwt_secreto,
            algorithms=[_cfg.jwt_algoritmo],
            options={"require": ["exp", "sub", "jti"]},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expirado", headers=cabecera)
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Token inválido", headers=cabecera)

    fila = db.execute(
        """
        SELECT u.id, u.username::text AS username, u.email::text AS email,
               r.id AS rol_id, r.nombre::text AS rol, st.jti
        FROM sesion_token st
        JOIN usuario u ON u.id = st.usuario_id
        JOIN rol r     ON r.id = u.rol_id
        WHERE st.jti = %s
          AND st.revocado = FALSE AND st.estado = TRUE AND st.expira_en > now()
          AND u.estado = TRUE AND r.estado = TRUE
          AND u.id = %s
        """,
        (carga["jti"], int(carga["sub"])),
    ).fetchone()
    if fila is None:
        raise HTTPException(401, "Sesión no vigente", headers=cabecera)
    return fila


def requerir_permiso(modulo: str, accion: str) -> Callable:
    """Fabrica una dependencia que exige un permiso sobre un modulo.

    El rol "admin" tiene acceso implicito a todos los modulos, incluso a
    los que se agreguen despues.
    """
    columna = ACCIONES[accion]
    consulta = sql.SQL(
        """
        SELECT mr.{col} AS permitido
        FROM modulo_rol mr
        JOIN modulo m ON m.id = mr.modulo_id
        WHERE mr.rol_id = %s AND m.nombre = %s
          AND mr.estado = TRUE AND m.estado = TRUE
        """
    ).format(col=sql.Identifier(columna))

    def dependencia(
        usuario: dict = Depends(usuario_actual),
        db: psycopg.Connection = Depends(get_db),
    ) -> dict:
        if usuario["rol"] == "admin":
            return usuario
        fila = db.execute(consulta, (usuario["rol_id"], modulo)).fetchone()
        if not fila or not fila["permitido"]:
            raise HTTPException(403, f"Sin permiso para '{accion}' en el modulo '{modulo}'")
        return usuario

    return dependencia
