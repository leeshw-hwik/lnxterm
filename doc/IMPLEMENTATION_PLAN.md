# LnxTerm 구현 계획

ST-Link V3 Mini 기반 임베디드 장치 디버깅/로그 수집용 시리얼 터미널 GUI.

## 현재 개발 기준
- 기준 버전: **v1.8.5**
- 이번 반영 목표:
  1. UI 다국어(한국어/영어) 적용
  2. 사용자 언어 선택/저장
  3. 첫 실행 기본 언어 영어화
  4. 메뉴 하이라이트 가독성 개선(VS Code Dark 계열)

## 기술 스택
- Python 3.12 + PyQt6 + pyserial + python-dotenv
- PyInstaller (`./build_exe.sh`)
- GitHub CLI(`gh`) 릴리스 관리

## 설계 개요

### 1) 다국어 계층
- `i18n.py` 신설
- `TRANSLATIONS`(ko/en) + `tr(language, key, **kwargs)` 헬퍼
- `normalize_language()`로 안전한 언어 코드 정규화

### 2) 언어 상태 관리
- `MainWindow`가 단일 언어 상태를 소유
- `QSettings("LnxTerm", "LnxTerm")`에 `language` 저장
- 앱 시작 시 저장값 로드, 없으면 `en`
- 메뉴(`Language`) 액션으로 언어 전환

### 3) 위젯별 적용 범위
- `MainWindow`
  - 메뉴, 상태 텍스트, 메시지박스, About, 시스템 메시지
- `SidebarWidget`
  - 그룹 타이틀, 툴팁, 카운터 상태/버튼/placeholder, 자동명령 목록
- `SearchWidget`
  - placeholder, 툴팁, 결과 없음 문구
- `AutomationDialog`
  - 그룹/라벨/placeholder/버튼 텍스트

### 4) 메뉴 스타일 개선
- `styles.py`에 메뉴 전용 색상 팔레트 추가
- 선택/눌림 상태에서 텍스트 색 명시 (`menu_text_active`)
- 배경 대비를 VS Code Dark 톤으로 보정

## 현재 핵심 기능 현황

| 기능 | 상태 |
|------|------|
| 시리얼 통신 | 포트 스캔/연결/해제/QThread 수신 |
| 자동 재연결 | 환경변수 기반 주기(`MS`/`SEC`), 기본 3초 |
| 로그 파일 | 세션 고정 파일 유지, 재연결 append 재개 |
| 문자열 통계 | 최대 10개, CSV 누적 기록 |
| 자동 명령 | 트리거 기반 사후 명령 실행 |
| 다국어 UI | 한국어/영어 전환 + 저장 복원 |
| 메뉴 가독성 | VS Code Dark 스타일 선택 대비 개선 |

## 후속 계획
1. i18n 키 분리(파일 분할) 및 누락 키 검사 자동화
2. `sidebar_widget.py` 대형 클래스 분리 리팩토링
3. 타겟 Linux 환경에서 Qt 의존성 경고(`libxcb-cursor`, `libtiff`) 점검
