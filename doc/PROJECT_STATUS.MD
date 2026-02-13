# 프로젝트 상태 보고서: LnxTerm (Project Status)

> **현재 버전**: v1.8.1
> **최종 업데이트**: 2026-02-13
> **타겟 시스템**: Linux (ST-Link V3 Mini 디버그 환경)

## 1) 프로젝트 개요
AI가 다음 세션에서 바로 작업을 이어갈 수 있도록 개발 상태를 정리한 문서이다.

## 2) 기술 스택
- Python 3.12+
- PyQt6 GUI (`styles.py`, 다크 테마)
- pyserial + pyserial-async 처리
- PyInstaller 배포
- GitHub CLI(`gh`) 릴리스 관리

## 3) 핵심 파일
- `main_window.py`: 전체 윈도우, 상태 전달, 통계 처리 연동
- `sidebar_widget.py`: 연결/로그/문자열 통계 UI 및 CSV 기록 로직
- `terminal_widget.py`: 터미널 표시, ANSI 하이라이트, 검색
- `search_widget.py`: Ctrl+F 검색 패널
- `styles.py`: One Dark Pro 기반 QSS
- `serial_manager.py`: 시리얼 수신 및 점유 감지 로직
- `log_manager.py`: 로그 파일 생성/flush/종료

## 4) 완료 항목

### A. 문자열 통계 CSV 정합성 [완료]
- 저장 열 순서 고정: `문자열, 집계 시점, 누적 카운트, 대소문자 구분, 로그`
- 로그 열에는 대상 문자열이 매칭된 **완전한 1줄 로그 원문** 저장
- `sidebar_widget.py` `_append_counter_stats()` 구현 반영

### B. 사이드바 UX 세부 개선 [완료]
- 문자열 통계 복사 버튼/로그 복사 버튼의 클릭성 및 정렬 조정
- 복사 대상 경로 표시 라인 정합성 유지

### C. 문서 정합성 정리 [완료]
- GEMINI.MD 규칙 적용으로 문서 이름을 대문자 MD로 통일:
  - `doc/IMPLEMENTATION_PLAN.MD`
  - `doc/PROJECT_STATUS.MD`
  - `doc/WALKTHROUGH.MD`
  - `doc/PROMPT.MD`
- 각 문서 v1.8.1 변경사항 반영

### D. 빌드/릴리스 [완료]
- `./build_exe.sh` 실행 성공
- `dist/lnxterm` 생성 완료

## 5) Known Issues / 주의점
- PyInstaller 빌드 경고: `libxcb-cursor.so.0`, `libtiff.so.5` 미탐지 경고
  - 실행 불가로 이어지지 않지만 타겟 시스템 패키지 상태에 따라 동작 영향 가능

## 6) 다음 세션 우선순위
1. `v1.8.1` GitHub Release 생성 후 실행 파일 업로드 여부 확인
2. 통계 CSV 샘플 샘플링(헤더/로그 라인) 테스트 자동화
3. 통계 초기화/재시작 시나리오에서 카운트 라벨 상태 동기화 추가 점검
4. GUI 접근성 개선: 작은 창에서 복사 버튼/텍스트 레이아웃 미세 정렬 유지

## 7) 명령 요약
```bash
./build_exe.sh
python -m py_compile main_window.py sidebar_widget.py styles.py search_widget.py terminal_widget.py
```
