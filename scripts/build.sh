#!/usr/bin/env bash
# macOS 빌드. 프로젝트 루트에서 `scripts/build.sh` 또는 어디서든 실행 가능.
#
# Tk가 포함된 Python 3.12 이상이 필요하다. asdf·pyenv로 설치한 파이썬과 macOS 기본 python3(3.9, Tk 8.5)는
# 대개 안 된다. `brew install python-tk@3.13` 또는 python.org 설치본을 쓰고, 자동 탐색이 안 맞으면
# `PYTHON=/경로/python3 scripts/build.sh`로 지정한다.
# Homebrew 파이썬은 시스템 site-packages에 pip 설치를 막으므로(PEP 668) .venv를 만들어 그 안에서 빌드한다.
set -euo pipefail
cd "$(dirname "$0")/.."

has_tk() {
  "$1" -c 'import sys, tkinter; sys.exit(0 if sys.version_info >= (3, 12) else 1)' >/dev/null 2>&1
}

find_python() {
  local p
  for p in "${PYTHON:-}" python3 /opt/homebrew/bin/python3.13 /opt/homebrew/bin/python3.12 \
           /Library/Frameworks/Python.framework/Versions/Current/bin/python3 /usr/local/bin/python3; do
    [ -n "$p" ] || continue
    command -v "$p" >/dev/null 2>&1 || continue
    if has_tk "$p"; then echo "$p"; return 0; fi
  done
  return 1
}

PY=$(find_python) || {
  echo "Tk가 포함된 Python 3.12 이상을 찾지 못했습니다. 'brew install python-tk@3.13' 후 다시 실행하거나" >&2
  echo "PYTHON=/경로/python3 scripts/build.sh 로 지정하세요." >&2
  exit 1
}
echo "python: $PY ($("$PY" --version 2>&1))"

if [ ! -x .venv/bin/python ] || ! has_tk .venv/bin/python; then
  rm -rf .venv
  "$PY" -m venv .venv
fi
.venv/bin/python -m pip install -q -r requirements.txt pyinstaller
.venv/bin/python -m PyInstaller PrintImg-mac.spec --noconfirm
echo "Built dist/PrintImg.app"
