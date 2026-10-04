#!/usr/bin/env bash
# Chạy trong bộ bàn giao: bash script.sh
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if command -v python3 >/dev/null 2>&1; then
  catalog_python=python3
elif command -v python >/dev/null 2>&1; then
  catalog_python=python
else
  echo 'Hãy cài Python 3.10 trở lên rồi chạy lại.' >&2
  exit 1
fi
"$catalog_python" -c 'import sys; assert sys.version_info >= (3, 10), "Cần Python 3.10 trở lên"'
if [[ ! -f .catalog-venv/bin/python && ! -f .catalog-venv/Scripts/python.exe ]]; then
  "$catalog_python" -m venv .catalog-venv
fi
catalog_venv_python=.catalog-venv/bin/python
if [[ -f .catalog-venv/Scripts/python.exe ]]; then
  catalog_venv_python=.catalog-venv/Scripts/python.exe
fi
"$catalog_venv_python" -m pip install -r requirements-catalog.txt
exec "$catalog_venv_python" script.py --worker "$@"
