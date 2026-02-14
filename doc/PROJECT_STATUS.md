# 프로젝트 상태 보고서: LnxTerm (Project Status)

> **현재 버전**: v1.8.3
> **최종 업데이트**: 2026-02-14
> **타겟 시스템**: Linux (ST-Link V3 Mini 디버그 환경)

## 1) 프로젝트 개요
ST-Link V3 Mini 기반 임베디드 장치 디버깅/로그 수집을 위한 PyQt6 시리얼 터미널 GUI.
다음 세션에서 즉시 작업 이어받을 수 있도록 구현/릴리스 상태를 요약한다.

## 2) 기술 스택
- Python 3.12+
- PyQt6
- pyserial
- python-dotenv
- PyInstaller
- GitHub CLI(`gh`)

## 3) 핵심 파일
- `main_window.py`: 전체 연결/재연결/로그 시작·중지/환경변수 로드/상태바
- `sidebar_widget.py`: 로그 경로/통계 경로 표시, 문자열 통계 카운터 및 CSV 기록
- `serial_manager.py`: 포트 스캔, 점유 감지(Lockfile + fuser), 읽기 스레드
- `log_manager.py`: 로그 파일 open/flush/close
- `terminal_widget.py`: RX/TX 표시 및 라인 파싱

## 4) v1.8.3 기준 완료 항목
1. `.env` 참조 경로 개선
- 배포 실행 파일(`dist/lnxterm`) 기준으로 `.env`를 우선 탐색
- 탐색 순서: 실행파일 디렉토리 → 현재 작업 디렉토리 → 소스 디렉토리
- `.env`가 없을 때 저장 경로도 실행 환경에 맞춰 결정

2. 자동 재연결 주기 환경변수화
- `RECONNECT_INTERVAL_MS`(우선) 또는 `RECONNECT_INTERVAL_SEC` 지원
- 값이 없거나 잘못되면 기본 3초(3000ms)
- 재연결 대기/실패 메시지에 실제 설정 주기 반영

3. 로그 파일 세션 고정
- 프로그램 실행 후 최초 지정된 로그 파일 경로를 세션 동안 유지
- 비정상 끊김 후 재연결 시 새 파일이 아닌 기존 파일에 append 재개

4. 문자열 통계 CSV 파일 세션 고정(로그 파일 기반)
- 통계 CSV 경로는 로그 파일 경로에서 계산되므로 세션 동안 동일 파일 유지
- 재연결 후에도 동일 CSV에 누적 기록

5. 연결만 끊었다 다시 연결하는 경우 UI 표시 유지
- 앱 재시작 없이 연결 해제/재연결 시 로그 파일/통계 파일 경로 표시 유지
- 명시적인 로그 중지 동작에서만 표시 초기화 가능

6. UI/UX 개선 (v1.8.3)
- ON/OFF 상태 라벨 테두리 제거 (텍스트만 표시)
- 문자열 통계 리셋 버튼 정렬 및 크기 통일
- 전체 초기화 버튼 잘림 현상 수정 (높이 20px)

## 5) Known Issues / 주의점
- PyInstaller 빌드 경고가 출력될 수 있음:
  - `libxcb-cursor.so.0`, `libtiff.so.5`
- 경고가 있어도 빌드 자체는 성공 가능. 타겟 시스템 라이브러리 설치 상태 점검 필요.

## 6) 다음 세션 우선순위
1. `v1.8.2` 릴리스 바이너리 실행 환경(타겟 Linux)에서 Qt 의존성 점검
2. 자동 재연결 시나리오(케이블 분리/복구) 통합 테스트 체크리스트 자동화
3. 문자열 통계 CSV 파일 잠금/동시성(장시간 운용) 안정성 점검

## 7) 핵심 점검 명령
```bash
.venv/bin/python -m py_compile main_window.py sidebar_widget.py serial_manager.py log_manager.py
./build_exe.sh
./dist/lnxterm
```
