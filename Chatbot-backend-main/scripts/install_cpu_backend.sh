#!/usr/bin/env bash
# -------------------------------------------------
# Chatbot-Backend CPU Only Setup Script
# -------------------------------------------------
# 1) removes existing venv (if any)
# 2) creates new venv
# 3) installs PyTorch CPU wheels first (avoid CUDA)
# 4) installs remaining dependencies w/o deps
# -------------------------------------------------
set -euo pipefail
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$BASE_DIR/venv"
REQ_FILE="$BASE_DIR/requirements.txt"

echo "🔄  Removing existing venv (if any)…"
rm -rf "$VENV_DIR"

echo "📦  Creating new virtualenv…"
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

pip install --upgrade pip --no-cache-dir

echo "🧠  Installing CPU-only PyTorch wheels…"
pip install --no-cache-dir \
  --extra-index-url https://download.pytorch.org/whl/cpu \
  torch==1.13.1+cpu torchvision==0.14.1+cpu torchaudio==0.13.1+cpu

echo "📚  Installing remaining dependencies (no deps)…"
pip install --no-cache-dir --no-deps -r "$REQ_FILE"

echo "✅  Setup complete.  Python binary: $(which python)"
python - << 'PY'
import torch, sys
print("Torch version:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())
PY

echo "🚀  You can now start the backend via PM2 or uvicorn." 