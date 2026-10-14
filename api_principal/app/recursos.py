"""Catalogo declarativo de recursos CRUD de la API.

Cada entrada genera, mediante app.crud.crear_router, los endpoints de una
tabla del modelo relacional. Las tablas con logica propia (usuarios con
contraseña, gateways con clave de API, lecturas generadas por la ingesta)
se ajustan con los parametros del recurso.
"""

from datetime import date, datetime

from app.crud import Campo, Recurso
from app.security import generar_hash, validar_longitud_clave


def _hash_usuario(datos: dict) -> dict:
    """Convierte el campo virtual 'password' en 'password_hash' (bcrypt)."""
    clave = datos.pop("password", None)
    if clave is not None:
        validar_longitud_clave(clave)
        datos["password_hash"] = generar_hash(clave)
    return datos


RECURSOS: list[Recurso] = [
    # ----------------------------- Seguridad -----------------------------
    Recurso(
        ruta="usuarios", tabla="usuario", modulo="usuarios",
        campos=[
            Campo("rol_id", int, requerido=True),
            Campo("username", str, requerido=True, min_len=3, max_len=50),
            Campo("email", str, max_len=100),
            Campo("nombre_completo", str, max_len=120),
            Campo("password", str, requerido=True, min_len=6, max_len=72, virtual=True),
        ],
        filtros=["rol_id"], proteger_propio=True, antes_guardar=_hash_usuario,
    ),
    Recurso(
        ruta="roles", tabla="rol", modulo="roles",
        campos=[
            Campo("nombre", str, requerido=True, max_len=50),
            Campo("descripcion", str, max_len=255),
        ],
    ),
    Recurso(
        ruta="modulos", tabla="modulo", modulo="modulos",
        campos=[
            Campo("nombre", str, requerido=True, max_len=50),
            Campo("ruta", str, requerido=True, max_len=100),
            Campo("descripcion", str, max_len=255),
        ],
    ),
    Recurso(
        ruta="permisos", tabla="modulo_rol", modulo="permisos",
        campos=[
            Campo("rol_id", int, requerido=True, editable=False),
            Campo("modulo_id", int, requerido=True, editable=False),
            Campo("puede_leer", bool),
            Campo("puede_crear", bool),
            Campo("puede_editar", bool),
            Campo("puede_eliminar", bool),
        ],
        filtros=["rol_id", "modulo_id"],
    ),
    # ----------------------------- Infraestructura -----------------------------
    Recurso(
        ruta="zonas", tabla="zona_manglar", modulo="zonas",
        campos=[
            Campo("nombre", str, requerido=True, max_len=100),
            Campo("descripcion", str, max_len=255),
            Campo("municipio", str, max_len=100),
            Campo("latitud", float),
            Campo("longitud", float),
        ],
    ),
    Recurso(
        ruta="tipos-nodo", tabla="tipo_nodo", modulo="tipos-nodo",
        campos=[
            Campo("codigo", str, requerido=True, max_len=20, mayusculas=True),
            Campo("nombre", str, requerido=True, max_len=100),
            Campo("descripcion", str, max_len=255),
        ],
    ),
    Recurso(
        ruta="nodos", tabla="nodo", modulo="nodos",
        campos=[
            Campo("codigo", str, requerido=True, max_len=20, mayusculas=True),
            Campo("nombre", str, max_len=100),
            Campo("tipo_nodo_id", int, requerido=True),
            Campo("zona_id", int),
            Campo("gateway_id", int),
            Campo("hardware", str, max_len=100),
        ],
        filtros=["tipo_nodo_id", "zona_id", "gateway_id"],
    ),
    # ----------------------------- Catalogos -----------------------------
    Recurso(
        ruta="unidades", tabla="unidad_medida", modulo="unidades",
        campos=[
            Campo("simbolo", str, requerido=True, max_len=20),
            Campo("nombre", str, requerido=True, max_len=60),
        ],
    ),
    Recurso(
        ruta="variables", tabla="variable", modulo="variables",
        campos=[
            Campo("codigo", str, requerido=True, max_len=30),
            Campo("nombre", str, requerido=True, max_len=100),
            Campo("descripcion", str, max_len=255),
            Campo("unidad_id", int, requerido=True),
            Campo("tipo_nodo_id", int),
            Campo("rango_min", float),
            Campo("rango_max", float),
        ],
        filtros=["tipo_nodo_id", "unidad_id"],
    ),
    Recurso(
        ruta="sensores", tabla="sensor", modulo="sensores",
        campos=[
            Campo("nodo_id", int, requerido=True),
            Campo("variable_id", int, requerido=True),
            Campo("modelo", str, requerido=True, max_len=60),
            Campo("fecha_instalacion", date),
        ],
        filtros=["nodo_id", "variable_id"],
    ),
    # ----------------------------- Datos (los crea la ingesta) -----------------------------
    Recurso(
        ruta="lecturas", tabla="lectura", modulo="lecturas",
        campos=[
            Campo("nodo_id", int, editable=False),
            Campo("gateway_id", int, editable=False),
            Campo("rssi", int, editable=False),
            Campo("snr", float, editable=False),
            Campo("latitud", float, editable=False),
            Campo("longitud", float, editable=False),
            Campo("satelites", int, editable=False),
            Campo("fecha_recepcion", datetime, editable=False),
        ],
        filtros=["nodo_id", "gateway_id"],
        permitir_crear=False, permitir_editar=False, orden_descendente=True,
    ),
    Recurso(
        ruta="mediciones", tabla="medicion", modulo="mediciones",
        campos=[
            Campo("lectura_id", int, editable=False),
            Campo("variable_id", int, editable=False),
            Campo("valor", float, editable=False),
        ],
        filtros=["lectura_id", "variable_id"],
        permitir_crear=False, permitir_editar=False, orden_descendente=True,
    ),
    # ----------------------------- Alertas -----------------------------
    Recurso(
        ruta="umbrales", tabla="umbral", modulo="umbrales",
        campos=[
            Campo("variable_id", int, requerido=True),
            Campo("nivel", str, requerido=True, max_len=15, mayusculas=True),
            Campo("minimo", float),
            Campo("maximo", float),
            Campo("mensaje", str, max_len=255),
        ],
        filtros=["variable_id", "nivel"],
    ),
    Recurso(
        ruta="alertas", tabla="alerta", modulo="alertas",
        campos=[
            Campo("medicion_id", int, editable=False),
            Campo("umbral_id", int, editable=False),
            Campo("mensaje", str, editable=False),
            Campo("atendida", bool),
        ],
        filtros=["medicion_id", "umbral_id", "atendida"],
        permitir_crear=False, orden_descendente=True,
    ),
]
