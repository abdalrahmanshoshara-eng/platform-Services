#!/usr/bin/env bash
# Restore a custom-format dump. Restores to a SEPARATE database by default to
# avoid clobbering your data. Pass --force-into "$POSTGRES_DB" to overwrite.
# Usage: scripts/restore_postgres.sh <dump-file> [target_db]
set -euo pipefail

DUMP="${1:?path to .dump file required}"
: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}"
HOST="${POSTGRES_HOST:-localhost}"
PORT="${POSTGRES_PORT:-5432}"
TARGET_DB="${2:-${POSTGRES_DB:-reports_db}_restore}"

if [ ! -f "$DUMP" ]; then echo "Dump not found: $DUMP" >&2; exit 1; fi

if [ "$TARGET_DB" = "${POSTGRES_DB:-}" ]; then
  echo "WARNING: about to restore INTO the live database '${TARGET_DB}'. This overwrites data."
  read -r -p "Type 'yes' to continue: " CONFIRM
  [ "$CONFIRM" = "yes" ] || { echo "Aborted."; exit 1; }
fi

export PGPASSWORD="$POSTGRES_PASSWORD"
echo "Ensuring target database '${TARGET_DB}' exists ..."
psql -h "$HOST" -p "$PORT" -U "$POSTGRES_USER" -d postgres \
  -tc "SELECT 1 FROM pg_database WHERE datname='${TARGET_DB}'" | grep -q 1 \
  || psql -h "$HOST" -p "$PORT" -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE \"${TARGET_DB}\""

echo "Restoring into '${TARGET_DB}' ..."
pg_restore -h "$HOST" -p "$PORT" -U "$POSTGRES_USER" -d "$TARGET_DB" \
  --no-owner --no-privileges --clean --if-exists "$DUMP"
echo "Restore complete into '${TARGET_DB}'."
