#!/usr/bin/env bash
# Timestamped PostgreSQL backup (custom format). Reads config from env / .env.
# Does NOT print the password. Usage: scripts/backup_postgres.sh
set -euo pipefail

: "${POSTGRES_DB:?POSTGRES_DB is required}"
: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}"
HOST="${POSTGRES_HOST:-localhost}"
PORT="${POSTGRES_PORT:-5432}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"

mkdir -p "$BACKUP_DIR"
TS="$(date +%Y%m%d-%H%M%S)"
OUT="${BACKUP_DIR}/${POSTGRES_DB}-${TS}.dump"

echo "Backing up '${POSTGRES_DB}' from ${HOST}:${PORT} ..."
PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
  -h "$HOST" -p "$PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  --format=custom --no-owner --no-privileges --file "$OUT"

echo "Backup written: $OUT"
echo "NOTE: this backs up the DATABASE only. Media files (generated reports) must be backed up separately, e.g.:"
echo "  tar czf ${BACKUP_DIR}/media-${TS}.tar.gz -C backend media   # or copy the docker 'backend_media' volume"
