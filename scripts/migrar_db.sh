#!/usr/bin/env bash
# Aplica las migraciones de base de datos a un despliegue existente.
#
# Los scripts de db/principal y db/auxiliar solo se ejecutan automaticamente la
# primera vez que se crea cada base. Para una base que ya tiene datos, este
# script aplica los archivos de migracion (04 en adelante en la principal y 02
# en adelante en la auxiliar). Son idempotentes: se pueden repetir sin dano.
#
# Uso (desde la raiz del proyecto, con docker compose en marcha):
#     bash scripts/migrar_db.sh
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "Falta el archivo .env (copiar .env.example)" >&2
  exit 1
fi
set -a
# shellcheck disable=SC1091
. ./.env
set +a

echo "== Base principal (PostgreSQL) =="
for f in db/principal/0[4-9]_*.sql db/principal/[1-9][0-9]_*.sql; do
  [ -f "$f" ] || continue
  echo "Aplicando $f"
  docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$f"
done

echo "== Base auxiliar (MySQL) =="
for f in db/auxiliar/0[2-9]_*.sql db/auxiliar/[1-9][0-9]_*.sql; do
  [ -f "$f" ] || continue
  echo "Aplicando $f"
  docker compose exec -T -e MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql mysql -u root "$MYSQL_DATABASE" < "$f"
done

echo "Migraciones aplicadas. Reconstruya la API con: docker compose up -d --build api api_aux"
