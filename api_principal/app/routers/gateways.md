# Modulo `app/routers/gateways.py`

Alta de gateways con generacion de clave de API y rotacion de la clave. Etiqueta `gateways`.

| Metodo | Ruta | Permiso | Descripcion |
|---|---|---|---|
| POST | `/api/gateways` | `gateways` / crear | Crea el gateway y devuelve su `api_key` una unica vez. |
| POST | `/api/gateways/{id}/rotar-clave` | `gateways` / editar | Genera una clave nueva e invalida la anterior. |
| GET, PUT, DELETE | `/api/gateways`, `/api/gateways/{id}` | segun accion | CRUD generico definido en este mismo modulo (listar, detalle, editar y eliminacion logica). |
| POST | `/api/gateways/{id}/restaurar` | `gateways` / editar | Restaura un gateway eliminado. |

## Seguridad
En la base de datos solo se guarda el hash SHA-256 de la clave; la clave en claro no se puede recuperar. El gateway la envia en la cabecera `X-API-Key` a `/api/ingest`.
