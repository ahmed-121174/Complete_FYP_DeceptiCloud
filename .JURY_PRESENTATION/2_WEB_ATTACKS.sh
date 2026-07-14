#!/usr/bin/env bash

PROJ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${PROJ}/venv/bin/activate" 2>/dev/null || true
exec bash "${PROJ}/attacks/web_attacks.sh" "$@"
