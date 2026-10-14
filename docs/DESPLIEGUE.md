# Guía de despliegue en el VPS (iotmangrove.info)

Datos del servidor: VPS Namecheap, IP 199.192.19.144. Registros DNS tipo A ya configurados: `@` y `www` apuntan a esa IP.

## Opción rápida: instalación automática desde GitHub

El script `scripts/instalar_vps.sh` hace por usted los pasos 1 a 5 de esta guía: instala Docker, descarga el código, abre el firewall, crea el `.env` con secretos aleatorios, emite el certificado HTTPS y levanta todos los servicios. Al terminar muestra la dirección, el usuario y la clave del administrador y la clave del gateway.

**A. Subir el proyecto a GitHub** (una sola vez, desde su equipo, dentro de la carpeta `iotmangrove`):
```bash
git init -b main
git add .
git commit -m "IoT-Mangrove: versión inicial"
git remote add origin https://github.com/USUARIO/REPOSITORIO.git
git push -u origin main
```
El `.gitignore` excluye `.env`, `certbot/` y `node_modules/`: ningún secreto sube a GitHub. Compruébelo con `git status` antes de hacer el `commit`.

**B. Ejecutar el instalador en el VPS** (conectado por SSH como root):
```bash
git clone https://github.com/USUARIO/REPOSITORIO.git /opt/iotmangrove
sudo bash /opt/iotmangrove/scripts/instalar_vps.sh --correo su_correo@ejemplo.com
```
Si el repositorio es público también puede descargar solo el script y ejecutarlo (revíselo antes con `less instalar_vps.sh`):
```bash
curl -fsSLO https://raw.githubusercontent.com/USUARIO/REPOSITORIO/main/scripts/instalar_vps.sh
sudo bash instalar_vps.sh --repo https://github.com/USUARIO/REPOSITORIO.git --correo su_correo@ejemplo.com
```

Opciones útiles: `--liberar-puertos` (detiene Apache o Nginx del sistema si ocupan el 80 o el 443), `--clave-admin` (define la contraseña del administrador en lugar de generarla), `--simular` (muestra los pasos sin ejecutarlos) y `--help`.

Es seguro ejecutarlo de nuevo: conserva el `.env` y el certificado, y solo actualiza el código y reconstruye. Para publicar cambios: haga `git push` desde su equipo y en el VPS ejecute `sudo bash /opt/iotmangrove/scripts/instalar_vps.sh`.

Si el repositorio es **privado**, el VPS necesita credenciales para clonarlo: use una llave de despliegue (*deploy key*) de solo lectura o un token de acceso de solo lectura, o haga el repositorio público mientras instala. No ponga contraseñas personales en la dirección.

> Requisitos: Ubuntu 22.04 o 24.04, el DNS de `iotmangrove.info` ya apuntando al VPS (el script lo verifica y se detiene si no coincide) y los puertos 80 y 443 libres.

Si prefiere el método manual, siga los pasos de abajo.

---

## 1. Preparar el servidor
```bash
ssh root@199.192.19.144
# Docker y el plugin de compose (si no estan instalados)
curl -fsSL https://get.docker.com | sh
docker compose version

# Firewall: solo SSH, HTTP y HTTPS
ufw allow 22/tcp && ufw allow 80/tcp && ufw allow 443/tcp && ufw --force enable

# Los puertos 80 y 443 deben estar libres (Apache, Nginx del sistema, etc.)
ss -tlnp | grep -E ':80 |:443 '
```
Verifique el DNS desde su equipo: `dig +short iotmangrove.info` debe devolver `199.192.19.144`.

## 2. Subir el proyecto
Desde su equipo (en la carpeta que contiene `iotmangrove/`):
```bash
scp -r iotmangrove root@199.192.19.144:/opt/
ssh root@199.192.19.144
cd /opt/iotmangrove
```

## 3. Crear el archivo de secretos
```bash
./scripts/generar_secretos.sh      # crea .env con claves aleatorias
nano .env                          # defina ADMIN_PASSWORD y ADMIN_EMAIL
```
Anote el valor de `GATEWAY_API_KEY`: es la clave que debe enviar el gateway.

> Las contraseñas que estaban escritas en el docker-compose anterior (`TuPasswordSegura123!`) y en los scripts SQL (`admin123`, etc.) ya no se usan. Si alguna vez se publicaron, considerelas comprometidas.

Opcional: si no quiere los 54 datos de demostración, elimine `db/principal/03_datos_demo.sql` antes del primer arranque.

## 4. Emitir el certificado HTTPS
```bash
./scripts/obtener_certificado.sh su_correo@ejemplo.com
```
Let's Encrypt valida el dominio por el puerto 80, por eso este paso va antes de levantar Nginx.

## 5. Levantar todo
```bash
docker compose up -d --build
docker compose ps          # los 5 servicios deben estar "running" / "healthy"
docker compose logs -f api # debe decir: "API iniciada"
```
En el primer arranque PostgreSQL y MySQL ejecutan los scripts de `db/` (esquema, semillas y datos de demostración) y la API crea el usuario administrador.

## 6. Verificar
```bash
curl https://iotmangrove.info/api/salud        # {"estado":"ok"}
curl https://iotmangrove.info/aux/salud        # {"estado":"ok"}
curl "https://iotmangrove.info/aux/chatbot/consultar?q=cual+es+el+ph+normal"
```
En el navegador:
- https://iotmangrove.info : inicio de sesión y panel
- https://iotmangrove.info/docs : documentación interactiva (Swagger) de la API principal
- https://iotmangrove.info/aux/ : indice de la API auxiliar

Prueba automatica completa (desde cualquier equipo con Python y `pip install httpx`):
```bash
python scripts/prueba_api.py https://iotmangrove.info SU_ADMIN_PASSWORD SU_GATEWAY_API_KEY
python scripts/prueba_api_aux.py https://iotmangrove.info https://iotmangrove.info/aux SU_ADMIN_PASSWORD
```

## 7. Renovación del certificado
El certificado dura 90 días. Programe la renovación semanal:
```bash
crontab -e
0 3 * * 1 /opt/iotmangrove/scripts/renovar_certificado.sh
```

## Operación
| Tarea | Comando |
|---|---|
| Ver registros | `docker compose logs -f api` |
| Reiniciar un servicio | `docker compose restart api` |
| Actualizar el codigo | `docker compose up -d --build` |
| Copia de seguridad de PostgreSQL | `docker compose exec -T postgres pg_dump -U $POSTGRES_USER $POSTGRES_DB > respaldo.sql` |
| Copia de seguridad de MySQL | `docker compose exec -T mysql mysqldump -u root -p"$MYSQL_ROOT_PASSWORD" $MYSQL_DATABASE > respaldo_aux.sql` |
| Borrar TODO (incluye los datos) | `docker compose down -v` |

Los scripts de `db/` solo se ejecutan cuando el volumen de datos esta vacío. Para cambiar el esquema en un servidor con datos, aplique los cambios con `psql` o `mysql` manualmente.

## Problemas frecuentes
- **Nginx no arranca:** falta el certificado (paso 4) o el puerto 80/443 esta ocupado.
- **La API reinicia en bucle:** revise `docker compose logs api`; suele faltar una variable de `.env` o `JWT_SECRET` tiene menos de 32 caracteres.
- **El certificado falla:** el DNS aun no propaga o el puerto 80 esta bloqueado en el firewall del proveedor.
