# LnxTerm 개발 워크스루

## 프로젝트 개요
ST-Link V3 Mini를 이용한 임베디드 장치 디버그/로그 수집용 시리얼 터미널 GUI 프로그램.

## 프로젝트 구조

```
lnxterm/
├── main.py              # 엔트리포인트
├── main_window.py       # 메인 윈도우 + .env/로그 관리
├── terminal_widget.py   # 타임스탬프 터미널 출력
├── search_widget.py     # Ctrl+F 검색
├── sidebar_widget.py    # 포트 설정 + 로그 정보 표시
├── serial_manager.py    # pyserial QThread 래핑
├── log_manager.py       # 로그 파일 관리
├── styles.py            # VS Code Dark+ QSS
├── requirements.txt     # 의존성
├── run.sh               # 실행 스크립트
├── .env                 # LOG_DIR 환경변수 (git/AI 제외)
├── .env.example         # .env 예제
├── .gitignore           # git 제외 목록
├── .antigravityignore   # AI 전송 제외 목록
├── GEMINI.MD            # 프로젝트 규칙
└── doc/
    ├── PROMPT.MD            # 프로그램 요구사항
    ├── implementation_plan.md  # 구현 계획
    └── walkthrough.md       # 개발 워크스루 (이 파일)
```

## 주요 기능
| 기능 | 설명 |
|------|------|
| 포트 연결 | `/dev/ttyACM*`, `/dev/ttyUSB*` 스캔 및 연결 |
| 자동 재연결 | 연결 끊김 시 3초 후 자동 재연결 |
| 명령 전송 | 하단 입력 바, ↑↓ 히스토리, Enter(LF) 전송, 빈 엔터 허용 |
| 타임스탬프 | `[YYYY-MM-DD HH:MM:SS.mmm]` 날짜+시간 밀리초 단위 |
| TX/RX 구분 | 접두사 없이 색상만 구분 (TX: 파란, RX: 초록) |
| 로그 저장 | `.env` LOG_DIR에 `lnxterm_YYYYMMDD_HHMMSS.log` 자동 생성 |
| 검색 | Ctrl+F 실시간 검색, F3/Shift+F3 이동 |
| 다크 테마 | VS Code Dark+ 색상 팔레트 |
| 보안 | `.env` 파일 git/AI 전송 제외 |

## 실행 방법

```bash
# 방법 1: 실행 스크립트 (venv 자동 생성)
./run.sh

# 방법 2: 직접 실행
.venv/bin/python main.py
```

## 검증 결과
- ✅ **구문 검증**: 모든 Python 파일 정상 파싱
- ✅ **의존성 설치**: PyQt6, pyserial, python-dotenv 설치 완료
- ✅ **앱 실행**: GUI 정상 구동 확인
- ✅ **시리얼 연결**: 디바이스 연결/해제/자동 재연결 동작 확인
- ✅ **로그 기록**: `lnxterm_YYYYMMDD_HHMMSS.log` 자동 생성 확인
- ✅ **`.env` 관리**: LOG_DIR 미설정 시 다이얼로그 → 자동 저장 확인
