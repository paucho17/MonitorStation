"""Recursos CRUD de las notificaciones (bitacora de avisos, solo lectura)."""

from app.crud import Campo, Recurso

RECURSOS_NOTIFICACIONES: list[Recurso] = [
    Recurso(
        ruta="notificaciones", tabla="notificacion", modulo="notificaciones",
        campos=[
            Campo("alerta_id", int, editable=False),
            Campo("usuario_id", int, editable=False),
            Campo("canal", str, editable=False),
            Campo("destino", str, editable=False),
            Campo("situacion", str, editable=False),
            Campo("detalle", str, editable=False),
        ],
        filtros=["alerta_id", "usuario_id", "canal", "situacion"],
        permitir_crear=False, permitir_editar=False, orden_descendente=True,
    ),
]
