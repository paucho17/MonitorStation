# Modulo `app/security.py`

Autenticacion, sesiones revocables y autorizacion por modulo.

## Flujo
1. `/api/auth/login` valida usuario y contrasena (bcrypt) y emite un JWT HS256 con `sub`, `username`, `rol`, `jti`, `iat` y `exp`.
2. El `jti` se guarda en la tabla `sesion_token`; el logout lo revoca antes de que expire.
3. En cada peticion protegida se valida firma, expiracion y vigencia del `jti`, y luego el permiso del rol sobre el modulo en `modulo_rol` (el rol `admin` tiene acceso total).

## Funciones
| Funcion | Descripcion |
|---|---|
| `configurar(cfg)` | Inyecta la configuracion desde `main.py`. |
| `validar_longitud_clave(clave)` | Rechaza contrasenas que superen el limite de 72 bytes de bcrypt. |
| `generar_hash(clave)` / `verificar_clave(clave, hash)` | Hash y verificacion bcrypt (con tiempo constante si el usuario no existe). |
| `generar_clave_api()` / `hash_clave_api(clave)` | Clave de API del gateway y su hash SHA-256 (solo el hash se guarda). |
| `emitir_token(db, usuario)` | Crea el JWT y registra la sesion. Devuelve el token y su duracion. |
| `usuario_actual(...)` | Dependencia que valida el JWT y devuelve el usuario autenticado. |
| `requerir_permiso(modulo, accion)` | Fabrica de dependencias: exige `puede_leer`, `puede_crear`, `puede_editar` o `puede_eliminar` sobre un modulo. |

## Respuestas de error
401 token ausente, invalido, expirado o revocado; 403 rol sin permiso sobre el modulo.
