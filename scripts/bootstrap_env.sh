#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONTRIB_DIR="${PROJECT_ROOT}/contrib/container"
COMPOSE_FILE="${CONTRIB_DIR}/docker-compose.yml"
ENV_FILE="${PROJECT_ROOT}/.env"
ENV_EXAMPLE="${PROJECT_ROOT}/.env.example"

if [[ ! -f "${COMPOSE_FILE}" ]]; then
  echo "Unable to find docker compose file at ${COMPOSE_FILE}" >&2
  exit 1
fi

if [[ ! -f "${ENV_EXAMPLE}" ]]; then
  echo "Missing ${ENV_EXAMPLE}. Generate it before bootstrapping." >&2
  exit 1
fi

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Creating ${ENV_FILE} from template"
  cp "${ENV_EXAMPLE}" "${ENV_FILE}"
fi

echo "Starting SiteLog stack via docker compose..."
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" up --build -d

echo "Applying database migrations..."
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" exec inventree-server invoke update

echo "To create a Django superuser run:"
echo "  docker compose --env-file ${ENV_FILE} -f ${COMPOSE_FILE} exec inventree-server invoke superuser"

echo "Bootstrap complete. Access the API at http://localhost:8080/api/ once credentials are ready."
echo "Call this command: curl -u <user>:<pass> http://localhost:8080/api"


