#!/usr/bin/env bash
set -euo pipefail

APP_TARGET="${1:-patient}"
PORT="${PORT:-8501}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

print_usage() {
  cat <<'EOF'
Usage:
  ./scripts/run_local.sh [patient|clinician|landing]

Environment variables:
  PORT=8501   Streamlit port
EOF
}

check_python_module() {
  local module="$1"
  python - <<PY
import importlib.util
import sys
sys.exit(0 if importlib.util.find_spec("$module") else 1)
PY
}

if [[ "$APP_TARGET" == "-h" || "$APP_TARGET" == "--help" || "$APP_TARGET" == "help" ]]; then
  print_usage
  exit 0
fi

if ! check_python_module streamlit; then
  echo "[ERROR] Missing dependency: streamlit"
  echo "Install dependencies first:"
  echo "  pip install -r requirements.txt"
  exit 1
fi

case "$APP_TARGET" in
  patient)
    ENTRYPOINT="apps/patient_app.py"
    ;;
  clinician)
    ENTRYPOINT="apps/clinician_app.py"
    ;;
  landing)
    ENTRYPOINT="app.py"
    ;;
  *)
    echo "[ERROR] Unknown app target: $APP_TARGET"
    print_usage
    exit 1
    ;;
esac

echo "[INFO] Starting $APP_TARGET app at http://localhost:$PORT"
exec python -m streamlit run "$ENTRYPOINT" --server.port "$PORT"
