# SiteLog Environment Overview

This guide describes how to stand up the SiteLog stack locally or in CI using the InvenTree container images.

## Stack Components

| Service | Definition | Notes |
| --- | --- | --- |
| PostgreSQL | `contrib/container/docker-compose.yml` service `inventree-db` | Uses `INVENTREE_DB_*` values from `.env` |
| Redis cache | `inventree-cache` | Optional but enabled by default |
| Django / API | `inventree-server` | Runs migrations via `invoke update` |
| Background worker | `inventree-worker` | Executes async jobs |
| Caddy proxy | `inventree-proxy` | Serves `/static`, `/media`, and reverse proxies API |

All services share variables from `.env`. Keep host paths absolute where possible (e.g., `INVENTREE_EXT_VOLUME=/srv/sitelog-data`) to avoid Docker Desktop/WSL path issues.

## Dependency Matrix

| Tooling | Version | Source |
| --- | --- | --- |
| Python | 3.11.x | `pyproject.toml` (`[tool.uv.pip].python-version`) |
| Pip | latest stable | Installed automatically in workflows |
| Node.js | 20.x LTS | Required by Vite 7 and React 19 frontend |
| Yarn | 1.x Classic | `src/frontend/yarn.lock` |
| Docker Engine | ≥ 24 / Compose v2 | Needed for `docker compose` |

## Bootstrap Workflow

1. `cp .env.example .env` (fill in passwords/paths). See `docs/config.md` for per-variable guidance.
2. `./scripts/bootstrap_env.sh`
   - Copies `.env` if missing.
   - Runs `docker compose -f contrib/container/docker-compose.yml up --build -d`.
   - Executes `invoke update` inside the `inventree-server` container for migrations/static files.
3. Create a Django superuser (interactive):  
   `docker compose --env-file .env -f contrib/container/docker-compose.yml exec inventree-server invoke superuser`
4. Verify the API responds:  
   `curl -u admin:ChangeMe123! http://localhost:8000/api/user/`

## Smoke Verification

After running the bootstrap script:

- `docker compose ps` shows all containers healthy.
- Visiting `http://localhost:8080` (Caddy proxy) renders the login page.
- `curl` request returns HTTP 200 with the authenticated user payload.

Log any deviations alongside remediation steps in `docs/phase1-checklist.md`.

## Troubleshooting

- **Migrations fail**: ensure `INVENTREE_DB_*` values in `.env` match the Postgres container defaults (`sitelog / sitelog / super-secret-password`).
- **Permission errors on volumes**: switch `INVENTREE_EXT_VOLUME` to an absolute path in your user directory.
- **Redis unavailable**: set `INVENTREE_CACHE_PORT` to an open port (>1024) or comment out the service in `docker-compose.yml` if truly unneeded.






