# Backup & restore (local)

Scripts live in `scripts/`. They read connection info from the environment / `.env`
and never print the password.

## Backup
```bash
set -a; . ./.env; set +a
POSTGRES_HOST=localhost scripts/backup_postgres.sh
# -> ./backups/reports_db-YYYYmmdd-HHMMSS.dump  (custom format)
```
The database dump does **not** include generated report files. Back media up separately:
```bash
tar czf backups/media-$(date +%Y%m%d-%H%M%S).tar.gz -C backend media
# or archive the docker 'backend_media' volume
```

## Verify a dump
```bash
scripts/verify_backup.sh backups/reports_db-XXXX.dump   # pg_restore --list integrity check
```

## Restore
Restores into a **separate** database by default (won't clobber your data):
```bash
set -a; . ./.env; set +a
POSTGRES_HOST=localhost scripts/restore_postgres.sh backups/reports_db-XXXX.dump
# restores into "<POSTGRES_DB>_restore"; pass a 2nd arg to choose the target DB
```
Restoring into the live DB requires typing `yes` at the confirmation prompt.

## Post-restore checks
```bash
# row counts / migration state against the restored DB
psql -h localhost -U "$POSTGRES_USER" -d "${POSTGRES_DB}_restore" -c "\dt reports_*"
DATABASE_URL=postgres://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:5432/${POSTGRES_DB}_restore \
  python backend/manage.py migrate --check
```

## Test status (honest)
The scripts pass `bash -n` syntax checks. An **actual backup→restore round-trip was NOT
executed** in the build environment because PostgreSQL was unavailable there. Run the steps
above once locally against your PostgreSQL and record the result here.
