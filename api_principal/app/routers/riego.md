# Modulo `app/routers/riego.py`

Prefijo `/api/riego`. Une el panel web con el controlador central de riego mediante una cola de ordenes.

## Panel web (JWT, modulo `riego`)
| Metodo | Ruta | Permiso | Descripcion |
|---|---|---|---|
| GET | `/api/riego/estado?ambito=` | leer | Zonas con modo, humedad actual, regado hoy, actuadores, ultimos riegos |
| PUT | `/api/riego/zonas/{id}/modo` | editar | Modo `AUTO`, `PROGRAMADO`, `MANUAL` o `APAGADO`. En `APAGADO` se ordena cerrar las valvulas |
| POST | `/api/riego/comandos` | crear | Orden manual `ABRIR` o `CERRAR` (duracion opcional) |
| GET | `/api/riego/comandos/{id}` | leer | Seguimiento de una orden |

Reglas de `ABRIR`: la zona debe estar en `MANUAL`; la duracion no puede superar `duracion_max_s`; se respeta el descanso entre riegos y el limite diario. `CERRAR` siempre se acepta.

## Controlador central (cabecera `X-API-Key`)
| Metodo | Ruta | Descripcion |
|---|---|---|
| GET | `/api/riego/central/pendientes` | Zonas con reglas y programas, y ordenes pendientes (pasan a `ENVIADO`). Las ordenes de mas de 10 minutos se cancelan |
| POST | `/api/riego/central/reporte` | Posiciones de actuadores, resultado de ordenes (`EJECUTADO`/`FALLIDO`) y riegos realizados |

## Ejemplo de reporte
```json
{
  "actuadores": [{"codigo": "V1", "posicion": "ABIERTA"}],
  "comandos": [{"id": 12, "situacion": "EJECUTADO"}],
  "eventos": [{"actuador": "V1", "inicio": "2026-10-16T14:00:00Z", "fin": "2026-10-16T14:02:00Z", "origen": "MANUAL"}]
}
```

El controlador aplica en sitio los enclavamientos de seguridad; el servidor solo valida de forma preventiva.
