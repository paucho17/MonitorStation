# Modulo `app/routers/auth.py`

Registro, inicio y cierre de sesion, y consulta del perfil. Prefijo `/api/auth`, etiqueta `auth`.

| Metodo | Ruta | Acceso | Descripcion |
|---|---|---|---|
| POST | `/api/auth/registro` | Publico (si `ALLOW_REGISTRATION=true`) | Crea un usuario con rol `consulta`. Rechaza usuarios o correos duplicados. |
| POST | `/api/auth/login` | Publico | Valida credenciales y devuelve `access_token` (JWT), tipo y duracion. |
| POST | `/api/auth/logout` | JWT | Revoca el `jti` del token actual. |
| GET | `/api/auth/me` | JWT | Devuelve el usuario, su rol y sus permisos por modulo. |

## Modelos
`RegistroIn` (`username`, `password` de 6 a 72 caracteres, `email` y `nombre_completo` opcionales) y `LoginIn` (`username`, `password`).

## Ejemplo
```bash
curl -X POST https://iotmangrove.info/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "su_clave"}'
```
