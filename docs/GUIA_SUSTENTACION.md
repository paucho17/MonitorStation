# Guía para la sustentación del parcial

## Qué mostrar (orden sugerido, unos 10 minutos)
1. **Resumen y arquitectura** (`RESUMEN_PROPUESTA.md`): problema, población y flujo nodo -> gateway -> API -> base de datos -> panel.
2. **Base de datos principal:** mostrar el diagrama de `MODELO_DATOS.md` y, en `psql`, que las 16 tablas tienen `estado`, `creado` y `actualizado`. Cambiar un registro y ver que `actualizado` cambia sin enviarlo.
3. **Swagger en `/docs`:** iniciar sesión en `POST /api/auth/login`, copiar el token en "Authorize" y probar:
   - `GET /api/dashboard` (lectura de datos).
   - `POST /api/zonas`, `PUT`, `DELETE` (queda `estado = false`), `incluir_inactivos=true` y `restaurar`.
4. **JWT y permisos:** con un usuario de rol `consulta` mostrar el 403 en `/api/usuarios`; con `admin` mostrar el acceso. Hacer logout y mostrar que el mismo token devuelve 401.
5. **Ingesta:** enviar una trama con `curl` (ver `GATEWAY.md`) con un pH de 9.4 y mostrar la alerta crítica generada en el dashboard.
6. **API auxiliar:** `GET /aux/chatbot/consultar?q=...` y un CRUD con JWT en `/aux/conocimiento`; mostrar la bitacora `/aux/consultas`.
7. **Despliegue:** `docker compose ps`, el candado HTTPS en https://iotmangrove.info y los puertos públicos (solo 80 y 443).

## Preguntas probables y respuestas cortas
- **¿Por qué un campo `estado` y no borrar?** Conserva el historial y la trazabilidad; el cliente ve el registro como eliminado, pero se puede restaurar. Lo manipula la API (`DELETE` y `restaurar`).
- **¿Quién llena `creado` y `actualizado`?** El motor: `DEFAULT now()` para `creado` y el trigger `trg_actualizado` para `actualizado` (en MySQL, `ON UPDATE CURRENT_TIMESTAMP`). La API nunca los envía.
- **¿Cómo funciona el JWT?** El login valida la contraseña (bcrypt) y firma un token HS256 con `sub`, `rol`, `jti` y `exp`. En cada petición se valida la firma, la expiración y que el `jti` no este revocado en `sesion_token`; luego se consulta `modulo_rol` para el permiso.
- **¿Qué es moduloxrol?** La tabla `modulo_rol`: relación muchos a muchos entre roles y módulos, con permisos de leer, crear, editar y eliminar.
- **¿Por qué el gateway no usa JWT?** Es un dispositivo sin sesión de usuario; se autentica con una clave de API propia (se guarda solo su hash SHA-256) que se puede rotar.
- **¿Por qué dos bases de datos?** La principal guarda la telemetría y la seguridad (PostgreSQL); la auxiliar guarda el conocimiento del chatbot (MySQL) y se puede escalar o cambiar de forma independiente.
- **¿Cómo se normalizó?** La tabla original `sensor_data` tenía una columna por sensor y casi todas nulas; ahora hay `lectura` (la trama) y `medicion` (una fila por variable), con catalogos de variable, unidad y tipo de nodo.
- **¿Por qué se retiró el MQ-135?** Su calefactor consume mucho y tarda en calentarse; se reemplaza por el SGP30 (eCO2 y TVOC, I2C, bajo consumo).
- **¿Qué limitaciones tiene?** La API auxiliar no consulta la revocación de sesiones de la principal (un token revocado vale alli hasta expirar); los umbrales son valores de referencia que deben validarse con la bibliografia; el panel actualiza por consulta periódica y no por WebSocket.

## Lista de verificación antes de entregar
- [ ] https://iotmangrove.info abre con HTTPS y muestra el login.
- [ ] `/docs` carga y el login devuelve un token.
- [ ] `python scripts/prueba_api.py ...` termina en 43/43.
- [ ] `python scripts/prueba_api_aux.py ...` termina en 22/22.
- [ ] El gateway real envio al menos una trama con `X-API-Key` y aparece en el dashboard.
- [ ] `.env` no esta en ningún repositorio ni se muestra en pantalla.
