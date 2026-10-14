# Modelo de datos

## Base principal (PostgreSQL): 16 tablas

Todas las tablas tienen `id` (llave primaria), `estado` (BOOLEAN, TRUE por defecto; FALSE = eliminado logicamente desde la API), `creado` (DEFAULT now()) y `actualizado` (mantenido por el trigger `trg_actualizado`).

| Grupo | Tabla | Campos únicos |
|---|---|---|
| Seguridad | `rol` | nombre |
| Seguridad | `usuario` | username, email |
| Seguridad | `modulo` | nombre, ruta |
| Seguridad | `modulo_rol` (moduloxrol) | (rol_id, modulo_id) |
| Seguridad | `sesion_token` | jti |
| Infraestructura | `zona_manglar` | nombre |
| Infraestructura | `gateway` | codigo, api_key_hash |
| Infraestructura | `tipo_nodo` | codigo |
| Infraestructura | `nodo` | codigo |
| Catalogos | `unidad_medida` | simbolo |
| Catalogos | `variable` | codigo |
| Catalogos | `sensor` | (nodo_id, variable_id, modelo) |
| Datos | `lectura` | - |
| Datos | `medicion` | (lectura_id, variable_id) |
| Alertas | `umbral` | (variable_id, nivel) |
| Alertas | `alerta` | (medicion_id, umbral_id) |

```mermaid
erDiagram
    rol ||--o{ usuario : "tiene"
    rol ||--o{ modulo_rol : "permisos"
    modulo ||--o{ modulo_rol : "permisos"
    usuario ||--o{ sesion_token : "sesiones"
    zona_manglar ||--o{ gateway : "contiene"
    zona_manglar ||--o{ nodo : "contiene"
    gateway ||--o{ nodo : "atiende"
    tipo_nodo ||--o{ nodo : "clasifica"
    tipo_nodo ||--o{ variable : "agrupa"
    unidad_medida ||--o{ variable : "mide en"
    nodo ||--o{ sensor : "instala"
    variable ||--o{ sensor : "mide"
    nodo ||--o{ lectura : "envia"
    gateway ||--o{ lectura : "recibe"
    lectura ||--o{ medicion : "contiene"
    variable ||--o{ medicion : "valor de"
    variable ||--o{ umbral : "limites"
    medicion ||--o{ alerta : "dispara"
    umbral ||--o{ alerta : "origina"
```

### Normalizacion
- **1FN:** no hay grupos repetidos. El diseno anterior tenía una columna por sensor (la mayoría nula segun el tipo de nodo); ahora cada valor medido es una fila de `medicion`.
- **2FN y 3FN:** los datos del nodo, del gateway, de la variable y de la unidad viven en su propia tabla y se referencian por llave foránea; ninguna columna depende de otra que no sea la llave. Los permisos se separan en `modulo_rol` (relación muchos a muchos entre rol y módulo).
- Agregar un sensor nuevo (por ejemplo salinidad) solo requiere insertar una fila en `variable`; no cambia el esquema.

## Base auxiliar (MySQL): 4 tablas

Con los mismos tres campos de auditoria (`estado` TINYINT, `creado`, `actualizado` con `ON UPDATE CURRENT_TIMESTAMP`).

| Tabla | Función | Campos únicos |
|---|---|---|
| `categoria_conocimiento` | Agrupa el conocimiento del chatbot | nombre |
| `referencia_variable` | Ficha de cada variable: descripción, uso y rango normal | codigo_variable |
| `conocimiento_chatbot` | Preguntas frecuentes y respuestas | pregunta |
| `consulta_chatbot` | Bitacora de lo que se pregunta al chatbot | - |

`referencia_variable.codigo_variable` coincide con `variable.codigo` de la base principal, de modo que las dos bases se corresponden sin necesidad de una llave foránea entre motores distintos.
