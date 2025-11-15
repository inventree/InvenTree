# SiteLog Configuration & Secrets

Use this document to map environment variables, understand where they are consumed, and decide how to source them in local, CI, or production deployments.

## Environment Variables

| Variable | Purpose | Required | Example / Default |
| --- | --- | --- | --- |
| `INVENTREE_TAG` | Container image tag for API + worker | Optional | `stable` |
| `INVENTREE_DEBUG` | Enables Django debug tooling | Optional | `True` for local |
| `INVENTREE_ALLOWED_HOSTS` | Comma-separated host list | Required | `localhost,127.0.0.1` |
| `INVENTREE_SITE_URL` | External URL served by Caddy | Required | `http://localhost` |
| `INVENTREE_SERVER` | Internal URL for proxy upstream | Required | `http://inventree-server:8000` |
| `INVENTREE_SECRET_KEY` | Django secret key | Required | `replace-this-secret-key` (generate per env) |
| `INVENTREE_DB_ENGINE` | Database backend driver | Required | `postgresql` |
| `INVENTREE_DB_HOST` | Database host reachable from containers | Required | `inventree-db` |
| `INVENTREE_DB_NAME` | Postgres database name | Required | `sitelog` |
| `INVENTREE_DB_USER` | Postgres user | Required | `sitelog` |
| `INVENTREE_DB_PASSWORD` | Postgres password | Required | `super-secret-password` |
| `INVENTREE_DB_PORT` | Host port for Postgres | Optional | `5432` |
| `INVENTREE_CACHE_PORT` | Host port for Redis | Optional | `6379` |
| `INVENTREE_HTTP_PORT` | Host port for HTTP proxy | Optional | `8080` |
| `INVENTREE_HTTPS_PORT` | Host port for HTTPS proxy | Optional | `8443` |
| `INVENTREE_EXT_VOLUME` | Host path for persistent data | Required | `./inventree-data` or `/srv/sitelog-data` |
| `DJANGO_SUPERUSER_USERNAME` | Default admin username (non-interactive runs) | Optional | `admin` |
| `DJANGO_SUPERUSER_EMAIL` | Default admin email | Optional | `admin@example.com` |
| `DJANGO_SUPERUSER_PASSWORD` | Default admin password | Optional | `ChangeMe123!` |

These entries are documented in `.env.example` and consumed automatically by `scripts/bootstrap_env.sh` and GitHub Actions.

## Secret Handling Strategy

### Local Development
- Copy `.env.example` to `.env`.
- Replace placeholder secrets (database password, `INVENTREE_SECRET_KEY`, admin credentials) with local values.
- Ensure `.env` remains untracked (`.gitignore` already skips it).

### GitHub Actions
- Store sensitive values under **Settings → Secrets and variables → Actions** in the repository.
- Recommended names:
  - `SITELOG_DB_PASSWORD` → used to populate `INVENTREE_DB_PASSWORD`.
  - `SITELOG_SECRET_KEY` → used for `INVENTREE_SECRET_KEY`.
  - `SITELOG_SUPERUSER_PASSWORD` → optional, consumed by management commands.
- Reference these secrets inside `.github/workflows/ci.yml` using `env:` blocks, e.g.:
  ```yaml
  env:
    INVENTREE_DB_PASSWORD: ${{ secrets.SITELOG_DB_PASSWORD }}
  ```

### Production / Staging
- Persist configuration outside the repo (e.g., AWS SSM Parameter Store, HashiCorp Vault, Doppler).
- Mount secrets via container orchestration (Docker Swarm, Kubernetes) or host-level `.env` files owned by the ops team.
- Keep `INVENTREE_EXT_VOLUME` on dedicated storage with routine backups; the path should include tenant data and attachments.

Document any deviations or per-environment overrides in this file so downstream teams can reproduce the configuration. When adding new variables, update `.env.example` and this table in the same change set.


