# Operations (local)

## Run the stack
```bash
cp .env.example .env         # edit secrets; never commit .env
docker compose up --build    # db, redis, backend (gunicorn), worker (celery), frontend
```
- Frontend: http://localhost:3000 · API: http://localhost:8000/api · Admin: /admin
- Health: `GET /health/live`, `GET /health/ready`.

## First-time data (explicit; never automatic)
```bash
docker compose run --rm backend python manage.py migrate
docker compose run --rm backend python manage.py seed_dev_data   # dev accounts + report types
```

## Celery worker
Runs as the `worker` service. Standalone: `celery -A config worker --loglevel=info`.
Recover stuck reports: `python manage.py recover_stuck_reports --minutes 30`.

## Tests / quality
See `testing-strategy.md`.

## Production-capable builds (not deployed)
- Backend image: `docker build ./backend` (gunicorn CMD + healthcheck).
- Frontend image: `docker build -f frontend/Dockerfile.prod ./frontend` (npm ci → build → start).

## Logging
JSON logs with `correlation_id`. Set `DJANGO_LOG_FORMAT=plain` for readable local logs,
`DJANGO_LOG_LEVEL=DEBUG` for verbosity.
