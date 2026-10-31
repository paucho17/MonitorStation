# Modulo `app/registro.py`

Lista los modulos funcionales de la API (`MODULOS`). Cada `ModuloApi` agrupa routers y recursos CRUD; `main.py` los recorre y los publica, por lo que agregar una funcion nueva no obliga a editar `main.py`.

| Modulo | Contenido |
|---|---|
| `nucleo` | auth, ingesta, dashboard/historial, gateways y los CRUD de catalogos (incluye ambitos y alias de variables) |
| `riego` | router `/api/riego` y los CRUD de zonas, actuadores, programas, ordenes y bitacora |

## Agregar un modulo nuevo
1. Crear su router (`app/routers/<nombre>.py`) y/o su lista de `Recurso`.
2. Declarar un `ModuloApi` en `MODULOS`.
3. Agregar una migracion SQL en `db/principal/` con sus tablas, su fila en `modulo`, los permisos en `modulo_rol` y los datos semilla.
