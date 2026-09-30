#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
export DB_USERNAME="${DB_USERNAME:-whattowatch}"
export APP_DEMO_DATA_ENABLED="${APP_DEMO_DATA_ENABLED:-true}"

if [[ -z "${DB_PASSWORD:-}" ]]; then
  read -r -s -p "MySQL password for ${DB_USERNAME}: " DB_PASSWORD
  printf '\n'
fi
export DB_PASSWORD

exec ./mvnw spring-boot:run
