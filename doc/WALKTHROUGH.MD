# LnxTerm 개발 워크스루

## 현재 릴리스
- 버전: **v1.8.2**
- 바이너리: `dist/lnxterm`

## 이번 릴리스 핵심 변경
1. `.env` 탐색 경로가 배포 실행 환경에 맞게 동작
2. 자동 재연결 주기를 `.env`로 조정 가능
3. 로그 파일/통계 CSV 파일이 세션 동안 고정 유지
4. 연결만 끊고 다시 연결해도 로그/통계 파일 표시 유지

## 점검 시나리오

### 1) `.env` 참조 확인
1. `dist/lnxterm` 옆에 `.env` 배치
2. `LOG_DIR`, `RECONNECT_INTERVAL_MS` 설정
3. 프로그램 시작 후 시스템 메시지의 `.env 경로` 확인

### 2) 재연결 주기 확인
1. 연결 후 장치 케이블 분리
2. 상태 메시지에서 설정한 주기(예: 2초/5초)로 재시도되는지 확인
3. 케이블 복구 후 자동 연결 복귀 확인

### 3) 로그/통계 파일 지속성 확인
1. 최초 연결 후 생성된 로그 파일/통계 파일 경로 확인
2. 연결만 수동 해제 후 다시 연결
3. 동일 경로 표시 유지 여부 확인
4. 새 로그 파일이 아닌 기존 파일에 append되는지 파일 타임라인 확인

## 실행/검증 명령
```bash
.venv/bin/python -m py_compile main_window.py sidebar_widget.py serial_manager.py log_manager.py
./build_exe.sh
./dist/lnxterm
```

## 참고
- PyInstaller 경고(`libxcb-cursor.so.0`, `libtiff.so.5`)가 있어도 빌드는 성공할 수 있음.
- 타겟 시스템 라이브러리 설치 여부는 별도 점검 필요.
