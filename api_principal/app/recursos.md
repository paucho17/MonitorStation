# Modulo `app/recursos.py`

Catalogo declarativo de los 14 recursos que reciben CRUD generico de `crud.py`. Cada uno corresponde a una tabla de la base de datos principal.

| Ruta (`/api/...`) | Tabla | Modulo de permisos |
|---|---|---|
| usuarios | usuario | usuarios |
| roles | rol | roles |
| modulos | modulo | modulos |
| permisos | modulo_rol | permisos |
| zonas | zona_manglar | zonas |
| tipos-nodo | tipo_nodo | tipos-nodo |
| nodos | nodo | nodos |
| unidades | unidad_medida | unidades |
| variables | variable | variables |
| sensores | sensor | sensores |
| lecturas | lectura | lecturas |
| mediciones | medicion | mediciones |
| umbrales | umbral | umbrales |
| alertas | alerta | alertas |

## Notas
- `usuarios` aplica un gancho que cifra la contrasena con bcrypt antes de guardar y nunca la devuelve.
- `gateways` no esta aqui: su alta genera la clave de API y se define en `routers/gateways.py`, que tambien declara su CRUD generico.
- Para agregar un recurso nuevo basta con anadir una entrada y un modulo en `db/principal/02_semillas.sql`.
