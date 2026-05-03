#!/usr/bin/env bash
# Готовит каталог /var/www/svorazbor для Docker Compose + GHCR (см. web/README.md).
#
# Запуск на VPS из корня клона репозитория:
#   git clone https://github.com/kaluginvit72/SVO_viplaty_site.git
#   cd SVO_viplaty_site
#   sudo bash deploy/scripts/setup-var-www-svorazbor.sh
#
# Либо скопируйте на сервер docker-compose.yml и этот скрипт и задайте:
#   export REPO_ROOT=/path/to/clone
#   sudo -E bash deploy/scripts/setup-var-www-svorazbor.sh

set -euo pipefail

APP_DIR="/var/www/svorazbor"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
REPO_ROOT="${REPO_ROOT:-$DEFAULT_REPO_ROOT}"

if [[ "${EUID:-0}" -ne 0 ]]; then
  echo "Запустите с правами root: sudo bash $0"
  exit 1
fi

DEPLOY_USER="${SUDO_USER:-root}"
if ! id -u "$DEPLOY_USER" &>/dev/null; then
  DEPLOY_USER="root"
fi

if [[ ! -f "${REPO_ROOT}/docker-compose.yml" ]]; then
  echo "Ошибка: не найден ${REPO_ROOT}/docker-compose.yml"
  echo "Укажите корень репозитория: export REPO_ROOT=/полный/путь && sudo -E bash $0"
  exit 1
fi

if [[ ! -f "${REPO_ROOT}/deploy/env.production.example" ]]; then
  echo "Ошибка: не найден ${REPO_ROOT}/deploy/env.production.example"
  exit 1
fi

mkdir -p "${APP_DIR}/data"

install -m 0644 "${REPO_ROOT}/docker-compose.yml" "${APP_DIR}/docker-compose.yml"
chown "${DEPLOY_USER}:${DEPLOY_USER}" "${APP_DIR}/docker-compose.yml"

if [[ ! -f "${APP_DIR}/.env" ]]; then
  install -m 0600 "${REPO_ROOT}/deploy/env.production.example" "${APP_DIR}/.env"
  chown "${DEPLOY_USER}:${DEPLOY_USER}" "${APP_DIR}/.env"
  echo "Создан ${APP_DIR}/.env — отредактируйте секреты (Telegram, при необходимости GA/YM)."
else
  echo "${APP_DIR}/.env уже существует — не перезаписываю."
fi

chown -R 1001:1001 "${APP_DIR}/data"
chown "${DEPLOY_USER}:${DEPLOY_USER}" "${APP_DIR}"
chmod 0755 "${APP_DIR}"

echo ""
echo "Каталог ${APP_DIR} готов."
echo "  • GitHub Actions → Secret VPS_APP_DIR = ${APP_DIR}"
echo "  • Дальше от пользователя ${DEPLOY_USER}: cd ${APP_DIR} && docker compose pull && docker compose up -d"
echo "  • Nginx: шаблон deploy/nginx/svorazbor.ru.conf"
