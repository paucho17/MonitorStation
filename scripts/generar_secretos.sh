#!/usr/bin/env bash
# Crea el archivo .env con secretos aleatorios a partir de .env.example.
set -euo pipefail
cd "$(dirname "$0")/.."

[ -f .env ] && { echo ".env ya existe; no se sobrescribe."; exit 1; }
cp .env.example .env

gen() { openssl rand -hex "$1"; }
sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$(gen 16)|" .env
sed -i "s|^MYSQL_PASSWORD=.*|MYSQL_PASSWORD=$(gen 16)|" .env
sed -i "s|^MYSQL_ROOT_PASSWORD=.*|MYSQL_ROOT_PASSWORD=$(gen 16)|" .env
sed -i "s|^JWT_SECRET=.*|JWT_SECRET=$(gen 32)|" .env
sed -i "s|^GATEWAY_API_KEY=.*|GATEWAY_API_KEY=$(gen 24)|" .env
chmod 600 .env

echo ".env generado. Falta definir ADMIN_PASSWORD (edite el archivo)."
echo "Clave del gateway (X-API-Key): $(grep ^GATEWAY_API_KEY= .env | cut -d= -f2)"
