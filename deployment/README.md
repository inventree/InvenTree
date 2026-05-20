# InvenTree Deployment

## What's in this directory

| File | Purpose |
|------|---------|
| `docker-compose.prod.yml` | Production stack (db, redis, gunicorn, worker, caddy proxy) |
| `.env.production` | Configuration template |
| `Caddyfile` | Reverse proxy config (Caddy) |
| `deploy.sh` | Build + start script |

## First-time setup

```bash
# 1. Create your env file from the template
cp deployment/.env.production deployment/.env

# 2. Edit deployment/.env with your production values
#    - Set INVENTREE_SITE_URL to your domain or IP
#    - Change INVENTREE_DB_PASSWORD
#    - Fill in PA_RECEIPT_API_ENDPOINT and PA_RECEIPT_API_KEY
#    - Optionally set INVENTREE_ADMIN_USER/INVENTREE_ADMIN_PASSWORD

# 3. Deploy
./deployment/deploy.sh
```

## Updating

```bash
# Rebuild + restart app containers (zero-downtime)
./deployment/deploy.sh --build
docker compose -f deployment/docker-compose.prod.yml up -d --no-deps inventree-server inventree-worker
```

## Useful commands

```bash
# View logs
docker compose -f deployment/docker-compose.prod.yml logs -f

# Service status
docker compose -f deployment/docker-compose.prod.yml ps

# Stop everything
docker compose -f deployment/docker-compose.prod.yml down

# Stop + wipe database volumes
docker compose -f deployment/docker-compose.prod.yml down -v
```

## Checklist

- [ ] `deployment/.env` created from `.env.production` template
- [ ] `INVENTREE_SITE_URL` set to your actual domain/IP
- [ ] `INVENTREE_DB_PASSWORD` changed from the default
- [ ] `PA_RECEIPT_API_*` values filled in (if using POS receipt feature)
- [ ] Firewall allows ports 80/443 (or `INVENTREE_HTTP_PORT`/`INVENTREE_HTTPS_PORT`)
