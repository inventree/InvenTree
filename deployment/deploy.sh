#!/usr/bin/env bash
# Build and start InvenTree locally (production stack).
#
# Usage:
#   ./deploy.sh          # Build image + start all services
#   ./deploy.sh --build  # Build image only (don't start)
#
# Prerequisites:
#   - Docker installed and running
#   - deployment/.env exists (copy .env.production → .env and fill in values)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEPLOY_DIR="$(cd "$(dirname "$0")" && pwd)"
IMAGE="inventree-local:latest"
COMPOSE_FILE="$DEPLOY_DIR/docker-compose.prod.yml"
ENV_FILE="$DEPLOY_DIR/.env"
DATA_DIR="$DEPLOY_DIR/inventree-data"
BUILD_ONLY=false

[[ "${1:-}" == "--build" ]] && BUILD_ONLY=true

# ---------- 1. Validate ----------
if [[ ! -f "$ENV_FILE" ]]; then
  echo "==> ERROR: $ENV_FILE not found."
  echo ""
  echo "    First time? Run:"
  echo "      cp deployment/.env.production deployment/.env"
  echo "    Then edit deployment/.env with your production values."
  exit 1
fi

# Source .env to check required vars are set (quietly)
set +e
# shellcheck source=/dev/null
source <(grep -v '^\s*#' "$ENV_FILE" | grep -v '^\s*$')
set -e

if [[ -z "${INVENTREE_EXT_VOLUME:-}" ]]; then
  echo "==> ERROR: INVENTREE_EXT_VOLUME is not set in .env"
  exit 1
fi

# ---------- 2. Create directories ----------
mkdir -p "$DATA_DIR" \
         "$DATA_DIR/redis" \
         "$DATA_DIR/static" \
         "$DATA_DIR/media"

# ---------- 3. Build ----------
echo "==> Building production image (target=production)..."
docker build \
  -t "$IMAGE" \
  --target production \
  -f "$REPO_ROOT/contrib/container/Dockerfile" \
  "$REPO_ROOT"

echo "==> Build complete."

# ---------- 4. Start (optional) ----------
if $BUILD_ONLY; then
  echo "==> Skipping start (--build only). To launch:"
  echo "    docker compose -f deployment/docker-compose.prod.yml up -d"
  exit 0
fi

echo "==> Starting services..."
docker compose -f "$COMPOSE_FILE" --project-directory "$DEPLOY_DIR" up -d

echo "==> Done. InvenTree should be available shortly."
echo "    Check logs:  docker compose -f deployment/docker-compose.prod.yml logs -f"
echo "    Status:      docker compose -f deployment/docker-compose.prod.yml ps"
