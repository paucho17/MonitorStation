#!/usr/bin/env bash
# =====================================================================
# IoT-Mangrove: instalador automático para un VPS Ubuntu 22.04 / 24.04
#
# Qué hace (en orden):
#   1. Instala las dependencias (git, curl, openssl, ufw, dnsutils) y Docker.
#   2. Clona el repositorio de GitHub en /opt/iotmangrove (o lo actualiza).
#   3. Abre el firewall (solo SSH, HTTP y HTTPS).
#   4. Crea el archivo .env con secretos aleatorios (si no existe).
#   5. Comprueba que el dominio apunte a este servidor.
#   6. Emite el certificado HTTPS de Let's Encrypt.
#   7. Levanta los servicios con Docker Compose y verifica que respondan.
#
# Es seguro ejecutarlo varias veces: no sobrescribe el .env existente ni
# vuelve a emitir un certificado vigente.
#
# Uso:
#   sudo bash instalar_vps.sh --repo https://github.com/USUARIO/REPO.git \
#                             --correo tu_correo@ejemplo.com
#
# Opciones:
#   --repo URL         Repositorio Git del proyecto (obligatorio la primera vez)
#   --correo CORREO    Correo para Let's Encrypt (obligatorio la primera vez)
#   --dominio NOMBRE   Dominio principal (por defecto: iotmangrove.info)
#   --rama NOMBRE      Rama a desplegar (por defecto: main)
#   --directorio RUTA  Carpeta de instalación (por defecto: /opt/iotmangrove)
#   --clave-admin TXT  Contraseña del administrador (si se omite, se genera)
#   --liberar-puertos  Detiene Apache/Nginx del sistema si ocupan 80 o 443
#   --simular          Muestra los pasos sin ejecutarlos (para probar)
#   -h, --help         Muestra esta ayuda
# =====================================================================
set -euo pipefail

REPO=""
CORREO=""
DOMINIO="iotmangrove.info"
RAMA="main"
DESTINO="/opt/iotmangrove"
CLAVE_ADMIN="${ADMIN_PASSWORD:-}"
LIBERAR_PUERTOS=0
SIMULAR=0

# ----------------------------- Utilidades -----------------------------
info()  { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
aviso() { printf '\033[1;33mAviso: %s\033[0m\n' "$*"; }
falla() { printf '\033[1;31mError: %s\033[0m\n' "$*" >&2; exit 1; }

# Ejecuta un comando, o solo lo muestra en modo --simular
ejecutar() {
  if [ "$SIMULAR" -eq 1 ]; then
    printf '[simulado] %s\n' "$*"
  else
    "$@"
  fi
}

uso() { sed -n '2,32p' "$0" | sed 's/^# \{0,1\}//'; exit 0; }

# ----------------------------- Argumentos -----------------------------
while [ $# -gt 0 ]; do
  case "$1" in
    --repo)            REPO="${2:?Falta el valor de --repo}"; shift 2 ;;
    --correo)          CORREO="${2:?Falta el valor de --correo}"; shift 2 ;;
    --dominio)         DOMINIO="${2:?Falta el valor de --dominio}"; shift 2 ;;
    --rama)            RAMA="${2:?Falta el valor de --rama}"; shift 2 ;;
    --directorio)      DESTINO="${2:?Falta el valor de --directorio}"; shift 2 ;;
    --clave-admin)     CLAVE_ADMIN="${2:?Falta el valor de --clave-admin}"; shift 2 ;;
    --liberar-puertos) LIBERAR_PUERTOS=1; shift ;;
    --simular)         SIMULAR=1; shift ;;
    -h|--help)         uso ;;
    *) falla "Opción desconocida: $1 (use --help)" ;;
  esac
done

if [ "$SIMULAR" -eq 0 ] && [ "$(id -u)" -ne 0 ]; then
  falla "Ejecute el script como root (anteponga sudo)."
fi

if [ "$SIMULAR" -eq 0 ] && [ -r /etc/os-release ]; then
  # shellcheck disable=SC1091
  . /etc/os-release
  case "${ID:-}" in
    ubuntu|debian) ;;
    *) falla "Sistema no soportado (${ID:-desconocido}). Use Ubuntu 22.04 o 24.04." ;;
  esac
fi

# ----------------------------- 1. Dependencias -----------------------------
info "1/7 Instalando dependencias del sistema"
export DEBIAN_FRONTEND=noninteractive
ejecutar apt-get update -y
ejecutar apt-get install -y git curl ca-certificates openssl ufw dnsutils

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  echo "Docker y Docker Compose ya están instalados."
else
  info "Instalando Docker"
  if [ "$SIMULAR" -eq 1 ]; then
    echo "[simulado] curl -fsSL https://get.docker.com | sh"
  else
    curl -fsSL https://get.docker.com -o /tmp/instalar_docker.sh
    sh /tmp/instalar_docker.sh
    rm -f /tmp/instalar_docker.sh
  fi
fi
ejecutar systemctl enable --now docker

# ----------------------------- 2. Código -----------------------------
info "2/7 Obteniendo el código desde GitHub"
if [ -d "$DESTINO/.git" ]; then
  echo "El repositorio ya existe en $DESTINO: se actualiza."
  ejecutar git -C "$DESTINO" fetch --all --prune
  ejecutar git -C "$DESTINO" checkout "$RAMA"
  ejecutar git -C "$DESTINO" pull --ff-only origin "$RAMA"
else
  [ -n "$REPO" ] || [ "$SIMULAR" -eq 1 ] || falla "Indique el repositorio con --repo https://github.com/USUARIO/REPO.git"
  ejecutar git clone --branch "$RAMA" --depth 1 "$REPO" "$DESTINO"
fi

if [ "$SIMULAR" -eq 1 ]; then
  # En simulación se trabaja sobre una copia temporal para poder probar el .env
  DESTINO="$(cd "$(dirname "$0")/.." && pwd)"
  echo "[simulado] se usa el proyecto local: $DESTINO"
fi
cd "$DESTINO"

# ----------------------------- 3. Firewall -----------------------------
info "3/7 Configurando el firewall (SSH, HTTP y HTTPS)"
ejecutar ufw allow 22/tcp
ejecutar ufw allow 80/tcp
ejecutar ufw allow 443/tcp
ejecutar ufw --force enable

# ----------------------------- 4. Secretos (.env) -----------------------------
info "4/7 Preparando el archivo de secretos (.env)"
CLAVE_GENERADA=0
if [ -f .env ]; then
  echo ".env ya existe: se conserva sin cambios."
else
  [ -n "$CORREO" ] || falla "Indique el correo con --correo (Let's Encrypt y administrador)."
  if [ -z "$CLAVE_ADMIN" ]; then
    CLAVE_ADMIN="$(openssl rand -base64 18 | tr -d '/+=' | cut -c1-16)A9"
    CLAVE_GENERADA=1
  fi
  bash ./scripts/generar_secretos.sh >/dev/null
  # '|' como delimitador: la clave nunca contiene ese carácter
  sed -i "s|^ADMIN_PASSWORD=.*|ADMIN_PASSWORD=${CLAVE_ADMIN}|" .env
  sed -i "s|^ADMIN_EMAIL=.*|ADMIN_EMAIL=${CORREO}|" .env
  chmod 600 .env
  echo ".env creado con secretos aleatorios (permisos 600)."
fi

# Carga los valores para el resumen final (sin exportarlos a otros procesos)
valor() { grep -E "^$1=" .env | head -n1 | cut -d= -f2-; }
CLAVE_ADMIN="$(valor ADMIN_PASSWORD)"
USUARIO_ADMIN="$(valor ADMIN_USERNAME)"
CLAVE_GATEWAY="$(valor GATEWAY_API_KEY)"
if grep -q "CAMBIAR" .env; then
  falla "El .env aún contiene valores 'CAMBIAR'. Edítelo (nano .env) y vuelva a ejecutar."
fi

# ----------------------------- 5. DNS y puertos -----------------------------
info "5/7 Comprobando DNS y puertos"
IP_PUBLICA="$(curl -fsS --max-time 8 https://api.ipify.org 2>/dev/null || true)"
IP_DOMINIO="$(dig +short "$DOMINIO" A 2>/dev/null | tail -n1 || true)"
echo "IP pública de este servidor: ${IP_PUBLICA:-no se pudo obtener}"
echo "IP a la que apunta $DOMINIO : ${IP_DOMINIO:-sin respuesta}"
if [ -n "$IP_PUBLICA" ] && [ -n "$IP_DOMINIO" ] && [ "$IP_PUBLICA" != "$IP_DOMINIO" ]; then
  falla "El dominio apunta a $IP_DOMINIO y este servidor es $IP_PUBLICA. Corrija el registro A en Namecheap y espere la propagación."
fi
[ -n "$IP_DOMINIO" ] || aviso "No se pudo resolver $DOMINIO; si falla el certificado, revise el DNS."

for puerto in 80 443; do
  if [ "$SIMULAR" -eq 0 ] && ss -ltn "sport = :$puerto" 2>/dev/null | grep -q LISTEN; then
    # Si ya corre nuestro propio nginx de Docker no es un conflicto
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q '^iot_nginx$'; then
      continue
    fi
    if [ "$LIBERAR_PUERTOS" -eq 1 ]; then
      aviso "Puerto $puerto ocupado: se detienen Apache y Nginx del sistema."
      systemctl disable --now apache2 nginx 2>/dev/null || true
    else
      falla "El puerto $puerto está ocupado. Libérelo o ejecute de nuevo con --liberar-puertos."
    fi
  fi
done

# ----------------------------- 6. Certificado HTTPS -----------------------------
info "6/7 Certificado HTTPS (Let's Encrypt)"
if [ -f "certbot/conf/live/${DOMINIO}/fullchain.pem" ]; then
  echo "Ya existe un certificado para ${DOMINIO}: no se vuelve a emitir."
else
  CORREO_CERT="${CORREO:-$(valor ADMIN_EMAIL)}"
  [ -n "$CORREO_CERT" ] || falla "Indique el correo con --correo."
  ejecutar bash ./scripts/obtener_certificado.sh "$CORREO_CERT"
fi

# ----------------------------- 7. Servicios -----------------------------
info "7/7 Construyendo y levantando los servicios (puede tardar varios minutos)"
ejecutar docker compose up -d --build

if [ "$SIMULAR" -eq 1 ]; then
  echo "[simulado] se omite la verificación de salud."
else
  echo "Esperando a que la API responda..."
  LISTO=0
  for _ in $(seq 1 60); do
    if curl -fsS --max-time 5 --resolve "${DOMINIO}:443:127.0.0.1" -k "https://${DOMINIO}/api/salud" >/dev/null 2>&1; then
      LISTO=1; break
    fi
    sleep 5
  done
  if [ "$LISTO" -ne 1 ]; then
    docker compose ps || true
    docker compose logs --tail=40 api || true
    falla "La API no respondió a tiempo. Revise los registros: docker compose logs api"
  fi
  docker compose ps
fi

# ----------------------------- Resumen -----------------------------
info "Instalación terminada"
cat <<RESUMEN

  Panel web ........ https://${DOMINIO}
  Documentación .... https://${DOMINIO}/docs
  API auxiliar ..... https://${DOMINIO}/aux/

  Administrador .... usuario: ${USUARIO_ADMIN}
                     clave:   ${CLAVE_ADMIN}
  Clave del gateway  (cabecera X-API-Key): ${CLAVE_GATEWAY}

  Estas claves están guardadas en ${DESTINO}/.env (permisos 600).
  Guárdelas en un lugar seguro y no las comparta ni las suba a GitHub.
RESUMEN
if [ "$CLAVE_GENERADA" -eq 1 ]; then
  aviso "La clave del administrador se generó automáticamente; cámbiela cuando lo desee."
fi

echo
echo "Para probar:  python3 scripts/prueba_api.py https://${DOMINIO} '${CLAVE_ADMIN}' '${CLAVE_GATEWAY}'"
echo "Actualizar:   sudo bash scripts/instalar_vps.sh   (vuelve a descargar y reconstruye)"
