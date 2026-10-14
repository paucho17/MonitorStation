# Modulo `app/db.py`

Acceso a PostgreSQL mediante `psycopg` 3 y un pool de conexiones.

## Funciones
| Funcion | Descripcion |
|---|---|
| `abrir_pool(cfg)` | Crea el pool (filas como diccionarios) y lo deja listo para usar. |
| `cerrar_pool()` | Cierra el pool al apagar la API. |
| `obtener_pool()` | Devuelve el pool o falla si no se inicializo. |
| `get_db()` | Dependencia de FastAPI: entrega una conexion; confirma la transaccion al terminar y hace rollback si hubo excepcion. |
| `traducir_error(exc)` | Convierte errores de PostgreSQL en `HTTPException`: 409 (valor unico duplicado), 400 (llave foranea, nulo, check o formato), 500 (resto). |

## Uso
Los routers reciben la conexion con `Depends(get_db)` y capturan `psycopg.Error` con `traducir_error`.
