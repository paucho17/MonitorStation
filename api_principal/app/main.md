# Modulo `app/main.py`

Punto de entrada de la API principal (FastAPI).

## Responsabilidad
- Crea la aplicacion FastAPI y registra los routers.
- Gestiona el ciclo de vida: al iniciar abre el pool de PostgreSQL y ejecuta `sembrar_datos_iniciales()`; al apagar cierra el pool.
- Publica el front-end estatico (`app/static/`) al final, para no tapar las rutas `/api`.

## Funciones
| Funcion | Descripcion |
|---|---|
| `sembrar_datos_iniciales()` | Crea el usuario administrador a partir de `ADMIN_USERNAME`, `ADMIN_EMAIL` y `ADMIN_PASSWORD` si no existe, y sincroniza la clave de API del gateway inicial (`GATEWAY_CODE`, `GATEWAY_API_KEY`). Es idempotente. |
| `ciclo_de_vida(app)` | Contexto asincrono de arranque y apagado. |
| `salud(db)` | `GET /api/salud`: comprueba que la API responde y que la base de datos esta disponible. |

## Rutas propias
| Metodo | Ruta | Acceso |
|---|---|---|
| GET | `/api/salud` | Publico |
| GET | `/docs`, `/redoc`, `/openapi.json` | Publico (documentacion generada por FastAPI) |

## Dependencias
`config.py`, `db.py`, `security.py`, `recursos.py`, `crud.py` y los routers de `routers/`.
