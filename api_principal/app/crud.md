# Modulo `app/crud.py`

Fabrica generica de routers CRUD. A partir de una descripcion declarativa (`Recurso`) genera los endpoints de un recurso con validacion, permisos y eliminacion logica.

## Elementos
| Elemento | Descripcion |
|---|---|
| `Campo` | Describe una columna: nombre, tipo, longitud maxima, si es editable, si se pasa a mayusculas, etc. |
| `Recurso` | Describe un recurso: ruta, tabla, modulo de permisos, campos, filtros y si permite crear. |
| `crear_router(r)` | Construye el `APIRouter` del recurso con prefijo `/api/{ruta}`. |

## Endpoints generados por recurso
| Metodo | Ruta | Permiso |
|---|---|---|
| GET | `/api/{ruta}` | leer (parametros `limite` de 1 a 500 con valor 100 por defecto, `desplazamiento`, `incluir_inactivos` y los filtros declarados) |
| GET | `/api/{ruta}/{id}` | leer |
| POST | `/api/{ruta}` | crear |
| PUT | `/api/{ruta}/{id}` | editar |
| DELETE | `/api/{ruta}/{id}` | eliminar (logico: `estado = false`) |
| POST | `/api/{ruta}/{id}/restaurar` | editar (`estado = true`) |

Nunca se borra fisicamente un registro. Las columnas `creado` y `actualizado` las gestiona la base de datos.
