#!/bin/bash
# LnxTerm 실행 스크립트
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

# venv가 없으면 생성
if [ ! -d "$VENV_DIR" ]; then
    echo "가상 환경 생성 중..."
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"
fi

# 실행
exec "$VENV_DIR/bin/python" "$SCRIPT_DIR/main.py" "$@"
