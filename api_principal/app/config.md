# Modulo `app/config.py`

Carga y valida la configuracion desde variables de entorno. No contiene valores por defecto para secretos.

## Elementos
| Elemento | Descripcion |
|---|---|
| `ConfiguracionError` | Excepcion lanzada cuando falta una variable obligatoria o es invalida. |
| `Configuracion` | Objeto con todos los parametros (base de datos, JWT, administrador, gateway, CORS, registro publico). |
| `cargar()` | Crea la configuracion; separada para facilitar las pruebas. |

## Variables relevantes
| Variable | Obligatoria | Uso |
|---|---|---|
| `JWT_SECRET` | Si (minimo 32 caracteres) | Firma de los tokens HS256. |
| `JWT_EXPIRE_MINUTES` | No (60) | Vigencia del token. |
| `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` | `ADMIN_PASSWORD` si | Administrador inicial. |
| `GATEWAY_CODE`, `GATEWAY_API_KEY` | No | Gateway inicial y su clave de API. |
| `ALLOW_REGISTRATION` | No (true) | Habilita el registro publico (rol `consulta`). |
| `CORS_ORIGINS` | No | Origenes permitidos, separados por coma. |

La plantilla de referencia esta en `.env.example` (raiz del proyecto).
