#!/usr/bin/env bash
# Validate a dump's integrity (table of contents) and print an object summary.
# Usage: scripts/verify_backup.sh <dump-file>
set -euo pipefail
DUMP="${1:?path to .dump file required}"
if [ ! -f "$DUMP" ]; then echo "Dump not found: $DUMP" >&2; exit 1; fi

echo "Verifying dump integrity: $DUMP"
if pg_restore --list "$DUMP" >/tmp/_toc.txt 2>/dev/null; then
  TABLES=$(grep -c "TABLE DATA" /tmp/_toc.txt || true)
  echo "OK: dump is readable. TABLE DATA entries: ${TABLES}"
else
  echo "FAILED: dump is not a valid custom-format archive." >&2
  exit 1
fi
