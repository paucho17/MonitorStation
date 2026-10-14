#!/usr/bin/env bash
# Emite el certificado Let's Encrypt de iotmangrove.info.
# Ejecutar UNA vez, antes de levantar nginx (necesita el puerto 80 libre).
set -euo pipefail

DOMINIO="iotmangrove.info"
CORREO="${1:?Uso: $0 correo@ejemplo.com}"

mkdir -p certbot/conf certbot/www

docker run --rm -p 80:80 \
  -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
  -v "$(pwd)/certbot/www:/var/www/certbot" \
  certbot/certbot certonly --standalone \
  -d "${DOMINIO}" -d "www.${DOMINIO}" \
  --agree-tos --no-eff-email -m "${CORREO}" --non-interactive

echo "Certificado emitido en certbot/conf/live/${DOMINIO}/"
