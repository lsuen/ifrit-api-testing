#!/usr/bin/env bash
# ifrit-apitest 全流程调试（Linux / macOS / WSL）
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  PYTHON=python
fi

echo "== ifrit-apitest debug workflow =="
echo "Root: $ROOT"
echo "Python: $PYTHON"

# WSL/Unix 下优先 curl 探测
exec "$PYTHON" scripts/debug_workflow.py --use-curl "$@"
