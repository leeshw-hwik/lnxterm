# LnxTerm 구현 계획

ST-Link V3 Mini를 통한 임베디드 장치 디버그/로그 수집용 시리얼 터미널 GUI 프로그램.

## 기술 스택
- Python 3 + PyQt6 + pyserial + python-dotenv

## 파일 구조

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
├── requirements.txt     # 의존성 (PyQt6, pyserial, python-dotenv)
├── run.sh               # 실행 스크립트
├── .env                 # LOG_DIR 환경변수 (git/AI 제외)
├── .env.example         # .env 예제
├── .gitignore           # git 제외 목록
├── .antigravityignore   # AI 전송 제외 목록
├── GEMINI.MD            # 프로젝트 규칙
└── doc/
    ├── PROMPT.MD            # 프로그램 요구사항
    ├── implementation_plan.md  # 구현 계획 (이 파일)
    └── walkthrough.md       # 개발 워크스루
```

## 핵심 기능

| 기능 | 설명 |
|------|------|
| 시리얼 통신 | 포트 스캔, 연결/해제, QThread 비동기 수신, LF 종료 |
| 자동 재연결 | 연결 끊김 시 3초 후 자동 재연결 + 로그 재개 |
| 터미널 출력 | `[YYYY-MM-DD HH:MM:SS.mmm]` 타임스탬프, TX(파란)/RX(초록) 색상 구분 |
| 로그 관리 | `.env`의 `LOG_DIR`에 `lnxterm_YYYYMMDD_HHMMSS.log` 자동 저장 |
| 검색 | Ctrl+F 검색, 하이라이트, 이전/다음 이동 |
| 명령 입력 | 하단 입력바, Enter 전송, 히스토리 (↑↓), 빈 엔터 허용 |

## 변경 이력
- **v1.0**: 초기 구현 (시리얼, 터미널, 검색, 로그, 명령)
- **v1.1**: LF 종료, 포커스 수정, 빈 엔터, CR 제거
- **v1.2**: TX 접두사 제거, 날짜 타임스탬프, 자동 재연결, 자동 로그
- **v1.3**: 자동 타임스탬프 파일명, 연결 시 필수 로그 지정
- **v1.4**: `.env` LOG_DIR, `lnxterm_날짜_시간.log` 자동 생성, 마크다운 재배치, 보안 설정
