#!/usr/bin/env bash
set -euo pipefail

: "${IMAGE_REF:?IMAGE_REF is required}"
COMPOSE_DIR="${COMPOSE_DIR:-/mnt/docker-data/inventree}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8086/web}"

SUDO=""
if [[ "$(id -u)" -ne 0 ]]; then
  if command -v sudo >/dev/null 2>&1; then
    SUDO="sudo"
  else
    echo "当前用户非 root 且无 sudo，无法执行部署命令" >&2
    exit 1
  fi
fi

cd "${COMPOSE_DIR}"

echo "部署目录: ${COMPOSE_DIR}"
echo "目标镜像: ${IMAGE_REF}"

${SUDO} cp .env ".env.bak.$(date +%Y%m%d-%H%M%S).actions"

if grep -q '^INVENTREE_IMAGE=' .env; then
  ${SUDO} sed -i "s#^INVENTREE_IMAGE=.*#INVENTREE_IMAGE=${IMAGE_REF}#" .env
else
  printf "\n# Fork image (managed by GitHub Actions)\nINVENTREE_IMAGE=%s\n" "${IMAGE_REF}" | ${SUDO} tee -a .env >/dev/null
fi

grep '^INVENTREE_IMAGE=' .env

${SUDO} docker compose pull inventree-server inventree-worker

# 在升级后先运行静态资源同步，避免前端哈希资源 404
${SUDO} docker compose run --rm inventree-server \
  sh -lc 'cd ${INVENTREE_BACKEND_DIR}/InvenTree && python3 manage.py compilemessages && python3 manage.py collectstatic --noinput'

${SUDO} docker compose up -d inventree-server inventree-worker

echo "等待服务健康..."
for i in $(seq 1 60); do
  code="$(curl -sSI "${HEALTH_URL}" | head -n1 || true)"
  echo "health[$i]: ${code}"

  if [[ "${code}" == *"200"* ]]; then
    echo "部署成功，健康检查通过"
    exit 0
  fi

  sleep 3
done

echo "部署失败：健康检查超时" >&2
${SUDO} docker logs --tail 150 inventree2-inventree-server-1 >&2 || true
${SUDO} docker logs --tail 120 inventree2-inventree-worker-1 >&2 || true
exit 1
