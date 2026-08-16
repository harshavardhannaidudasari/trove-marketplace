#!/bin/sh
set -e

host="${DATABASE_HOST:-db}"
port="${DATABASE_PORT:-5432}"

echo "Waiting for Postgres at ${host}:${port}..."
until pg_isready -h "$host" -p "$port" -q; do
  sleep 1
done
echo "Postgres is up."

alembic upgrade head

if [ "${SEED_ON_START:-true}" = "true" ]; then
  python -m app.seed.seed || true
fi

exec "$@"
