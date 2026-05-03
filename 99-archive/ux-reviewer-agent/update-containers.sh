#!/usr/bin/env bash
# update-containers.sh — pull образов с Docker Hub и перезапуск контейнеров при изменениях.
# Запуск: вручную или по cron. Путь проекта: PROJECT_DIR (по умолчанию /root/ux-reviewer).

set -e

DOCKERHUB_USER="${DOCKERHUB_USER:-kaluginvit}"
PROJECT_DIR="${PROJECT_DIR:-/root/ux-reviewer}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.hub.yml}"
BACKEND_SERVICE="backend"
FRONTEND_SERVICE="frontend"
BACKEND_IMAGE="${DOCKERHUB_USER}/backend:latest"
FRONTEND_IMAGE="${DOCKERHUB_USER}/frontend:latest"

cd "$PROJECT_DIR" || { echo "[$(date -Iseconds)] Ошибка: каталог $PROJECT_DIR не найден." >&2; exit 1; }
LOG_FILE="${LOG_FILE:-$PWD/update.log}"
if [ -f .env ]; then set -a; source .env; set +a; fi
DOCKERHUB_USER="${DOCKERHUB_USER:-kaluginvit}"

log() { echo "[$(date -Iseconds)] $*" | tee -a "$LOG_FILE"; }

backend_old_id=""
frontend_old_id=""
cid_backend=$(docker compose -f "$COMPOSE_FILE" ps -q "$BACKEND_SERVICE" 2>/dev/null || true)
cid_frontend=$(docker compose -f "$COMPOSE_FILE" ps -q "$FRONTEND_SERVICE" 2>/dev/null || true)
[ -n "$cid_backend" ] && backend_old_id=$(docker inspect -f '{{.Image}}' "$cid_backend" 2>/dev/null || true)
[ -n "$cid_frontend" ] && frontend_old_id=$(docker inspect -f '{{.Image}}' "$cid_frontend" 2>/dev/null || true)

log "Выполняю docker compose pull..."
docker compose -f "$COMPOSE_FILE" pull 2>&1 | tee -a "$LOG_FILE" || { log "Ошибка при pull."; exit 1; }

backend_new_id=""
frontend_new_id=""
docker image inspect "$BACKEND_IMAGE" &>/dev/null && backend_new_id=$(docker image inspect -f '{{.Id}}' "$BACKEND_IMAGE" 2>/dev/null || true)
docker image inspect "$FRONTEND_IMAGE" &>/dev/null && frontend_new_id=$(docker image inspect -f '{{.Id}}' "$FRONTEND_IMAGE" 2>/dev/null || true)

backend_updated=false
frontend_updated=false
[ -z "$backend_old_id" ] || [ "$backend_old_id" != "$backend_new_id" ] && backend_updated=true
[ -z "$frontend_old_id" ] || [ "$frontend_old_id" != "$frontend_new_id" ] && frontend_updated=true

[ "$backend_updated" = true ] && log "Backend: образ обновлён."
[ "$frontend_updated" = true ] && log "Frontend: образ обновлён."

if [ "$backend_updated" = true ] || [ "$frontend_updated" = true ]; then
  log "Перезапуск контейнеров..."
  docker compose -f "$COMPOSE_FILE" down 2>&1 | tee -a "$LOG_FILE" || true
  docker compose -f "$COMPOSE_FILE" up -d 2>&1 | tee -a "$LOG_FILE"
  log "Готово."
else
  log "Изменений нет."
fi
