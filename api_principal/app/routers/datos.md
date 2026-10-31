# Modulo `app/routers/datos.py`

Consulta de datos para el panel web. Prefijo `/api`, etiqueta `datos`.

| Metodo | Ruta | Permiso | Descripcion |
|---|---|---|---|
| GET | `/api/dashboard` | `dashboard` / leer | Ultima medicion de cada variable por nodo, ultima lectura recibida, ultima posicion GPS conocida y numero de alertas pendientes. |
| GET | `/api/historial` | `historial` / leer | Mediciones historicas con filtros. |

## Parametros de `/api/historial`
| Parametro | Descripcion |
|---|---|
| `nodo` | Codigo del nodo, por ejemplo `0xAA`. |
| `variable` | Codigo de la variable, por ejemplo `ph`. |
| `desde`, `hasta` | Rango de fechas. |
| `limite` | Cantidad maxima de filas (1 a 2000, por defecto 200). |
| `desplazamiento` | Filas a omitir (paginacion). |

## Filtro por ambito
`/api/dashboard` y `/api/historial` aceptan `ambito=VIVERO,RIEGO` (codigos de la tabla `ambito`, separados por coma). Sin el parametro, o con `todos`, no se filtra. Cada fila devuelve su `ambito`.
