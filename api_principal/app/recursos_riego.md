# Modulo `app/recursos_riego.py`

Recursos CRUD del sistema de riego, generados por `app.crud.crear_router` (eliminacion logica, filtros y paginacion como el resto).

| Ruta | Tabla | Notas |
|---|---|---|
| `/api/zonas-riego` | `zona_riego` | Reglas de la zona. El `modo` solo cambia con `PUT /api/riego/zonas/{id}/modo` |
| `/api/actuadores` | `actuador` | Valvulas y bomba. `posicion` la reporta el controlador |
| `/api/programas-riego` | `programa_riego` | Horarios; `dias` es una cadena de 7 caracteres (lunes a domingo) |
| `/api/comandos-riego` | `comando_riego` | Solo lectura: las ordenes se crean en `/api/riego/comandos` |
| `/api/eventos-riego` | `evento_riego` | Solo lectura: los reporta el controlador |

Los permisos de cada ruta son los modulos del mismo nombre en la tabla `modulo`.
