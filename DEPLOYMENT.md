# Deployment

The production stack is defined in `docker-compose.prod.yml`:

| Service | Role |
|---|---|
| `postgres` | PostgreSQL 17 (persistent volume) |
| `redis` | cache, Celery broker, Channels layer |
| `web` | Gunicorn + Uvicorn worker serving `config.asgi` (HTTP + WebSockets) |
| `celery-worker` | async tasks (certificates, email) |
| `celery-beat` | scheduled rollups (`DatabaseScheduler`) |
| `nginx` | TLS termination point, static/media serving, reverse proxy |

## Bring it up

```bash
cp .env.example .env      # set production secrets
make prod-build
make prod-up
```

The `web` entrypoint (`docker/django/entrypoint.prod.sh`) waits for the database,
applies migrations and runs `collectstatic` before starting Gunicorn. nginx serves
`/static/` and `/media/` from shared volumes and proxies everything else, upgrading
`/ws/` connections for WebSockets.

## Environment

`config.settings.production` is selected via `DJANGO_SETTINGS_MODULE`. All config
comes from environment variables (see `.env.example`). Required in production:

- `SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`
- `DB_*`, `REDIS_URL`, `CELERY_BROKER_URL`, `CHANNELS_REDIS_URL`
- `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`
- `EMAIL_*` for transactional email
- `AWS_*` to serve media from S3-compatible storage (otherwise local filesystem)

Production settings enforce HTTPS redirect, HSTS, secure cookies, content-type
nosniff and a referrer policy. Static files are served via WhiteNoise's compressed
manifest storage.

## Health checks

`GET /healthz` verifies database and cache connectivity and returns `200`/`503`.
The `web` service uses it as its Docker healthcheck; point your load balancer or
orchestrator probes at the same endpoint.

## Observability

Logging is structured via `structlog` (`django-structlog` attaches request IDs).
Emit JSON in production by shipping stdout to your log pipeline. Celery task state
is persisted via `django-celery-results`.

## Backups

- **Database**: schedule `pg_dump` against the `postgres` volume (e.g. nightly to
  object storage); the schema is migration-driven so restores are deterministic.
- **Media**: back the `media_data` volume, or prefer S3 storage which provides its
  own durability and versioning.

## Scaling

- Scale `web` and `celery-worker` horizontally; both are stateless (state lives in
  Postgres and Redis). Run exactly one `celery-beat`.
- Move Redis and PostgreSQL to managed/HA services for production traffic.
- Front the stack with a TLS-terminating load balancer; nginx already sets the
  forwarded-proto headers Django expects.
