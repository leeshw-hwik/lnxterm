#!/bin/bash
# LnxTerm 단독 실행 파일 빌드 스크립트

# 가상환경 활성화
source .venv/bin/activate

# 이전 빌드 아티팩트 삭제
rm -rf build dist lnxterm.spec

# PyInstaller를 사용하여 단독 실행 파일 생성
# --onefile: 모든 파일을 하나로 묶음
# --windowed: GUI 앱으로 실행 (터미널 창 열리지 않음)
# --name lnxterm: 실행 파일 이름 지정
# --clean: 캐시 삭제 후 빌드
pyinstaller --onefile --windowed --name lnxterm --clean main.py

echo "------------------------------------------------"
echo "빌드가 완료되었습니다. 실행 파일 위치: dist/lnxterm"
echo "------------------------------------------------"
