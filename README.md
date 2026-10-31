# IoT-Mangrove

Sistema telemático para el monitoreo ambiental de manglares: nodos LoRa (LilyGO T-Beam) -> gateway -> API en la nube -> panel web y chatbot.

## Estructura
```
iotmangrove/
  docker-compose.yml        Despliegue completo (6 servicios)
  docker-compose.local.yml  Desarrollo local con recarga en caliente (puertos publicados)
  frontend/                 SvelteKit: panel web (22 componentes, servicios api_<tabla>, DataTables)
  .env.example              Plantilla de variables y secretos
  db/principal/             PostgreSQL: esquema, semillas, migraciones (04 riego, 05 notificaciones y rol vivero)
  db/auxiliar/              MySQL: esquema (4 tablas) y base de conocimiento
  api_principal/            FastAPI: JWT, CRUD, ingesta, dashboard, alertas con aviso por correo
    app/*.py y app/routers/*.py   Cada modulo tiene su documento .md en la misma carpeta
  api_auxiliar/             Express: CRUD y buscador para el chatbot
  nginx/                    Proxy inverso con HTTPS
  scripts/                  Secretos, certificado HTTPS y pruebas automaticas
  docs/                     Resumen, modelo de datos, endpoints, despliegue, gateway, sustentacion
```

## Inicio rápido
Instalación automática en un VPS Ubuntu (instala Docker, genera secretos, emite el certificado y levanta todo):
```bash
sudo bash scripts/instalar_vps.sh --repo https://github.com/USUARIO/REPOSITORIO.git --correo correo@ejemplo.com
```
O paso a paso:
```bash
./scripts/generar_secretos.sh        # crea .env
nano .env                            # defina ADMIN_PASSWORD
./scripts/obtener_certificado.sh correo@ejemplo.com
docker compose up -d --build
```
Detalle completo en `docs/DESPLIEGUE.md`.

## Desarrollo local con Docker
```bash
cp .env.example .env && bash scripts/generar_secretos.sh
docker compose -f docker-compose.yml -f docker-compose.local.yml up --build
# Panel http://localhost:5173  |  API http://localhost:5000/docs
```
Detalle del panel en `docs/FRONTEND.md`.

## Desarrollo local sin Docker
```bash
# API principal (requiere PostgreSQL con los scripts de db/principal aplicados)
cd api_principal && pip install -r requirements.txt
export DB_HOST=localhost DB_NAME=iotmangrove DB_USER=... DB_PASSWORD=... \
       JWT_SECRET=$(openssl rand -hex 32) ADMIN_PASSWORD=... GATEWAY_API_KEY=...
uvicorn app.main:app --reload --port 5000

# API auxiliar (requiere MySQL con db/auxiliar aplicado)
cd api_auxiliar && npm install
DB_HOST=localhost DB_USER=... DB_PASSWORD=... DB_NAME=... JWT_SECRET=<el mismo> npm start
```

## Agente revisor
El archivo `.claude/agents/revisor-iotmangrove.md` define un agente de Claude Code que audita el
proyecto contra las reglas del parcial (campos de auditoría, JWT, eliminación lógica, secretos,
código sin emojis y documentado). Se apoya en la verificación automática:
```bash
python3 scripts/verificar_reglas.py
```
Al abrir la carpeta del proyecto en Claude Code, pídele: "usa el agente revisor-iotmangrove para revisar los cambios".

## Pruebas
```bash
pip install httpx
python scripts/prueba_api.py http://localhost:5000 ADMIN_PASSWORD GATEWAY_API_KEY
python scripts/prueba_api_aux.py http://localhost:5000 http://localhost:3000 ADMIN_PASSWORD
```
