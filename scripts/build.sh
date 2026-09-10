#!/usr/bin/env bash
# macOS 빌드. 프로젝트 루트에서 `scripts/build.sh` 또는 어디서든 실행 가능.
set -euo pipefail
cd "$(dirname "$0")/.."

python3 -m pip install -r requirements.txt pyinstaller
python3 -m PyInstaller PrintImg-mac.spec --noconfirm
echo "Built dist/PrintImg.app"
