#!/bin/bash
set -euo pipefail

cd /opt/lb-quotes
echo "[$(date -Iseconds)] Deploy start"

if [ ! -d .git ]; then
  echo "Not a git repo. Cloning repository..."
  git clone https://github.com/allenkaiyzhang/longbridge-trading-learning.git .
fi

git fetch --all -p
git checkout main
git pull --ff-only

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
. .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

sudo -n systemctl restart lb-quotes 2>/dev/null || echo "systemd restart skipped"

echo "[$(date -Iseconds)] Deploy done"
