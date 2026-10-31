"""Recursos CRUD del sistema de riego.

Se registran desde app.registro junto con el router de app.routers.riego.
Las tablas con logica propia (comandos y eventos, que crean el panel y el
controlador) quedan en solo lectura.
"""

from datetime import datetime, time

from app.crud import Campo, Recurso

RECURSOS_RIEGO: list[Recurso] = [
    Recurso(
        ruta="zonas-riego", tabla="zona_riego", modulo="zonas-riego",
        campos=[
            Campo("codigo", str, requerido=True, max_len=20, mayusculas=True),
            Campo("nombre", str, requerido=True, max_len=100),
            Campo("descripcion", str, max_len=255),
            Campo("ambito_id", int, requerido=True),
            Campo("nodo_sensor_id", int),
            Campo("variable_id", int),
            Campo("humedad_min", float),
            Campo("humedad_max", float),
            Campo("duracion_max_s", int),
            Campo("descanso_min_s", int),
            Campo("limite_diario_s", int),
            Campo("modo", str, editable=False),   # se cambia en /api/riego/zonas/{id}/modo
        ],
        filtros=["ambito_id", "modo"],
    ),
    Recurso(
        ruta="actuadores", tabla="actuador", modulo="actuadores",
        campos=[
            Campo("codigo", str, requerido=True, max_len=20, mayusculas=True),
            Campo("nombre", str, requerido=True, max_len=100),
            Campo("tipo", str, requerido=True, max_len=10, mayusculas=True),
            Campo("zona_riego_id", int),
            Campo("hardware", str, max_len=100),
            Campo("posicion", str, editable=False),          # la reporta el controlador
            Campo("ultimo_reporte", datetime, editable=False),
        ],
        filtros=["zona_riego_id", "tipo", "posicion"],
    ),
    Recurso(
        ruta="programas-riego", tabla="programa_riego", modulo="programas-riego",
        campos=[
            Campo("zona_riego_id", int, requerido=True),
            Campo("hora_inicio", time, requerido=True),
            Campo("duracion_s", int, requerido=True),
            Campo("dias", str, min_len=7, max_len=7),
            Campo("habilitado", bool),
        ],
        filtros=["zona_riego_id", "habilitado"],
    ),
    Recurso(
        ruta="comandos-riego", tabla="comando_riego", modulo="comandos-riego",
        campos=[
            Campo("actuador_id", int, editable=False),
            Campo("accion", str, editable=False),
            Campo("duracion_s", int, editable=False),
            Campo("origen", str, editable=False),
            Campo("usuario_id", int, editable=False),
            Campo("situacion", str, editable=False),
            Campo("detalle", str, editable=False),
        ],
        filtros=["actuador_id", "situacion", "origen"],
        permitir_crear=False, permitir_editar=False, orden_descendente=True,
    ),
    Recurso(
        ruta="eventos-riego", tabla="evento_riego", modulo="eventos-riego",
        campos=[
            Campo("actuador_id", int, editable=False),
            Campo("zona_riego_id", int, editable=False),
            Campo("inicio", datetime, editable=False),
            Campo("fin", datetime, editable=False),
            Campo("duracion_s", int, editable=False),
            Campo("origen", str, editable=False),
            Campo("motivo", str, editable=False),
        ],
        filtros=["actuador_id", "zona_riego_id", "origen"],
        permitir_crear=False, permitir_editar=False, orden_descendente=True,
    ),
]
