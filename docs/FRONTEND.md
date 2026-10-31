# Frontend (SvelteKit)

Panel web de IoT-Mangrove en `frontend/`. Es una aplicacion de una sola pagina (SvelteKit 3 con `adapter-static`): el JWT se guarda en `sessionStorage` y todas las llamadas van a `/api/*` (API principal) y `/aux/*` (chatbot) en el mismo dominio, por lo que no se necesita CORS.

## Estructura

```
frontend/
  src/lib/
    components/        22 componentes reutilizables (ver abajo)
    servicios/         cliente.js (fetch + JWT), api_<tabla>.js (un servicio CRUD por tabla),
                       datos.js (dashboard, historial, riego, perfil), tablas.js (catalogo)
    estado/sesion.svelte.js   sesion, usuario y permisos por modulo
    styles/global.css  tokens de diseno y modo oscuro
    index.js           barrel: import { Button, Card } from '#lib'
  src/routes/
    (auth)/login, (auth)/registro
    (app)/+layout.svelte      proteccion de rutas, menu segun permisos, chatbot
    (app)/+page.svelte        panel (ultimo dato por variable, alertas, GPS)
    (app)/historial           filtros + DataTables + CSV
    (app)/alertas             pendientes/atendidas, marcar atendida
    (app)/riego               zonas, modo, mando manual, bitacora
    (app)/perfil              avisos de alertas por correo
    (app)/admin               indice de tablas administrables
    (app)/[tabla]             lista CRUD de cualquier tabla del catalogo
    (app)/[tabla]/[item]      +layout.svelte (carga) y +page.svelte (formulario crear/editar)
  Dockerfile, Dockerfile.dev, nginx.conf
```

Componentes (`src/lib/components/`): Alert, Badge, Button, Card, Checkbox, Chatbot, Container, Footer, FormularioCrud, Grid, Header, Hero, Input, Medidor, Modal, Navbar, Section, Select, Sidebar, Spinner, TablaDatos, Tabs.

## Roles y permisos

El menu y los botones salen de `GET /api/auth/me` (permisos por modulo: leer, crear, editar, eliminar). La API vuelve a validar cada peticion, asi que ocultar un boton es comodidad y no seguridad.

| Rol | Que ve y hace |
|---|---|
| admin | Todo, incluidos usuarios, roles y permisos |
| operador | Infraestructura, catalogos, umbrales, alertas y riego |
| vivero | Panel, historial, atiende alertas, opera riego y programas |
| consulta | Solo lectura de panel, historial, alertas y catalogos publicos |

Los permisos se editan en la tabla `permisos` desde el propio panel. Interaccion entre roles: el operador o el vivero atienden las alertas que el admin y los demas ven; las ordenes de riego del vivero quedan en la bitacora que lee el operador.

## Agregar una tabla al panel

1. Declarar su recurso en la API (`recursos*.py`) y su modulo de permisos en una migracion.
2. Agregar una entrada en `src/lib/servicios/tablas.js` (columnas y campos del formulario).
3. Crear `src/lib/servicios/api_<tabla>.js` con `crearServicio('<ruta>')` y registrarlo en `servicios/index.js`.

Las rutas `/<tabla>`, `/<tabla>/nuevo` y `/<tabla>/<id>` quedan funcionando.

## Desarrollo local

Con Docker (recomendado; levanta bases de datos, APIs y panel con recarga en caliente):

```bash
cp .env.example .env && bash scripts/generar_secretos.sh   # solo la primera vez
docker compose -f docker-compose.yml -f docker-compose.local.yml up --build
# Panel: http://localhost:5173   API: http://localhost:5000/docs
```

Sin Docker (APIs ya corriendo en 5000 y 3000):

```bash
cd frontend && npm install && npm run dev
```

## Produccion

`docker compose up -d --build` construye el frontend (Node -> archivos estaticos -> Nginx) y el Nginx principal enruta `/api`, `/docs` a FastAPI, `/aux` a Express y `/` al panel. Ver `DESPLIEGUE.md`.
