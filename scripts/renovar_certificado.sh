#!/usr/bin/env bash
# Renueva el certificado sin detener el servicio (metodo webroot).
# Programar con cron, por ejemplo:  0 3 * * 1  /ruta/al/proyecto/scripts/renovar_certificado.sh
set -euo pipefail
cd "$(dirname "$0")/.."

docker run --rm \
  -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
  -v "$(pwd)/certbot/www:/var/www/certbot" \
  certbot/certbot renew --webroot -w /var/www/certbot --quiet

docker compose exec nginx nginx -s reload
