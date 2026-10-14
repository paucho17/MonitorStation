# Endpoints

La documentación interactiva de la API principal esta en `/docs` (Swagger). Las rutas protegidas exigen `Authorization: Bearer <JWT>`.

## API principal (FastAPI)

### Autenticación
| Método | Ruta | Acceso | Descripción |
|---|---|---|---|
| POST | /api/auth/registro | Público | Crea un usuario con rol `consulta` |
| POST | /api/auth/login | Público | Devuelve el JWT |
| POST | /api/auth/logout | JWT | Revoca el token actual |
| GET | /api/auth/me | JWT | Perfil y permisos del usuario |

### Ingesta y datos
| Método | Ruta | Acceso | Descripción |
|---|---|---|---|
| POST | /api/ingest | Cabecera X-API-Key | Recibe una trama del gateway |
| GET | /api/dashboard | JWT, módulo `dashboard` | Último valor de cada variable por nodo, GPS y alertas pendientes |
| GET | /api/historial | JWT, módulo `historial` | Historial. Filtros: `nodo`, `variable`, `desde`, `hasta`, `limite`, `desplazamiento` |
| GET | /api/salud | Público | Estado del servicio y de la base de datos |

### CRUD (todos con eliminación lógica)
Cada recurso ofrece: `GET /api/<r>` (lista), `GET /api/<r>/{id}`, `POST /api/<r>`, `PUT /api/<r>/{id}`, `DELETE /api/<r>/{id}` (pone `estado = false`) y `POST /api/<r>/{id}/restaurar`. La lista acepta `incluir_inactivos=true`, `limite` y `desplazamiento`.

| Recurso | Módulo (permisos) | Filtros | Notas |
|---|---|---|---|
| usuarios | usuarios | rol_id | La contraseña (`password`) se guarda con bcrypt y nunca se devuelve |
| roles | roles | - | |
| modulos | modulos | - | |
| permisos | permisos | rol_id, modulo_id | Tabla `modulo_rol` |
| zonas | zonas | - | |
| gateways | gateways | zona_id | `POST` devuelve la clave de API una sola vez; `POST /api/gateways/{id}/rotar-clave` genera otra |
| tipos-nodo | tipos-nodo | - | |
| nodos | nodos | tipo_nodo_id, zona_id, gateway_id | |
| unidades | unidades | - | |
| variables | variables | tipo_nodo_id, unidad_id | |
| sensores | sensores | nodo_id, variable_id | |
| lecturas | lecturas | nodo_id, gateway_id | Solo lectura y eliminación lógica (las crea la ingesta) |
| mediciones | mediciones | lectura_id, variable_id | Solo lectura y eliminación lógica |
| umbrales | umbrales | variable_id, nivel | |
| alertas | alertas | medicion_id, umbral_id, atendida | `PUT` solo para marcar `atendida` |

### Roles por defecto
| Rol | Alcance |
|---|---|
| admin | Acceso total a todos los módulos |
| operador | CRUD de zonas, nodos, sensores y umbrales; atiende alertas; lee catalogos y datos |
| consulta | Solo lectura de dashboard, historial, alertas y catalogos públicos |

Los permisos se editan en la tabla `modulo_rol` (recurso `permisos`).

### Códigos de respuesta
200/201 correcto, 400 datos inválidos, 401 sin sesión o token invalido/expirado/revocado, 403 sin permiso, 404 no existe, 409 valor único duplicado.

## API auxiliar (Express), publicada bajo `/aux`
Lectura pública en categorías, referencias y conocimiento. Toda escritura exige JWT de la API principal con rol `admin` u `operador`.

| Método | Ruta | Acceso | Descripción |
|---|---|---|---|
| GET | /aux/salud | Público | Estado del servicio |
| GET | /aux/chatbot/consultar?q=texto | Público | Respuesta del chatbot a una pregunta |
| POST | /aux/chatbot/consultar | Público | Igual, con cuerpo `{"q": "...", "origen": "tidio"}` (webhook) |
| GET | /aux/referencias/codigo/{codigo} | Público | Ficha de una variable (p. ej. `ph`) |
| CRUD | /aux/categorias | Lectura pública | Categorías de conocimiento |
| CRUD | /aux/referencias | Lectura pública | Fichas de variables |
| CRUD | /aux/conocimiento | Lectura pública | Preguntas y respuestas |
| GET / DELETE | /aux/consultas | JWT (borrar: admin) | Bitacora de consultas |

Los CRUD tienen las mismas operaciones y la misma eliminación lógica que la API principal (`DELETE` y `/{id}/restaurar`).

### Conexión con Tidio
El endpoint `POST /aux/chatbot/consultar` esta pensado para que el chatbot lo invoque como webhook o petición HTTP, enviando el texto del visitante en `q` y mostrando el campo `respuesta` del JSON. Verifique en su plan de Tidio que la automatizacion permite llamadas HTTP; si no, el mismo contenido puede cargarse manualmente en Tidio a partir de `GET /aux/conocimiento`.
