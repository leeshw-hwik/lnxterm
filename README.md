# LnxTerm (Serial Terminal for Linux)

ST-Link V3 Mini 기반 임베디드 장치 디버깅/로그 수집용 시리얼 터미널 GUI입니다.
- 현재 작업 기준 버전: **v1.10.0**

## 버전 선정 이유
- `v1.10.0`은 신규 기능(매크로 등록/실행 창) 추가와 동작 정책 개선(환경변수 자동 생성/저장, 자동 명령 실행 제어) 중심 업데이트입니다.
- 기존 인터페이스와 사용 방식의 하위 호환은 유지되어 **Minor 버전 상승**이 적절합니다.

## 핵심 기능
- 시리얼 포트 자동 탐색 (`/dev/ttyACM*`, `/dev/ttyUSB*`)
- 포트 점유 감지 (Lockfile + `fuser`/`lsof` + `TIOCEXCL`)
- 연결 끊김 시 자동 재연결 (기본 1초, `.env` 설정 가능)
- 로그 파일 자동 생성 및 절대 경로 표시/복사
- 문자열 통계(최대 10개) 카운팅/시작/정지/초기화 (`Last Detected` 표시)
- 문자열 통계 CSV 자동 기록
- 자동 명령(트리거/지연/명령 간격/즉시 중지, `sleep(ms)` 지원)
- 자주 쓰는 명령어(매크로) 등록/실행 (최대 1000개, 단축키 10개)
- 터미널 검색 (`Ctrl+F`), 하이라이트, 이전/다음 이동
- 다국어 지원(한국어/English) + 메뉴 언어 전환 저장

## v1.10.0 변경 요약
1. 환경변수 관리
- `.env` 미존재 시 실행 시점 자동 생성
- 최초 생성 시 자동 재연결 기본값을 `RECONNECT_INTERVAL_MS=1000`으로 고정
- 통계/자동 명령/매크로 변경 시 `.env` 즉시 반영

2. 자동 명령/통계 실행 정책 강화
- 미연결 상태에서는 자동 명령/문자열 통계 시작 차단
- 자동 명령 `Stop` 시 예약된 지연 실행까지 즉시 중지
- 시작 시 자동 명령이 자동으로 활성화되지 않도록 로딩 정책 보정
- 자동 명령 세트에서 `sleep(ms)` 구문 지원

3. 매크로 기능 추가
- 상단 자동 명령 아이콘 우측에 매크로 아이콘 추가
- 별도 창에서 명령어/설명 등록, 번호 클릭 즉시 전송
- 메인 창과 동시 사용 가능한 모델리스 창

4. UI 동작 개선
- 앱이 비활성 -> 활성으로 전환되면 명령 입력창 자동 포커스

## 빠른 실행 (릴리스 바이너리)
1. 실행 권한 부여
```bash
chmod +x lnxterm
```
2. 실행
```bash
./lnxterm
```

## 소스에서 실행
```bash
chmod +x run.sh
./run.sh
```

## 빌드
```bash
./build_exe.sh
```

빌드 결과물: `dist/lnxterm`

## 환경 설정 (`.env`)
```env
LOG_DIR=/your/custom/log/path
RECONNECT_INTERVAL_MS=1000
# RECONNECT_INTERVAL_SEC=1
AUTO_LOAD_MODE=CONFIRM
AUTO_LOAD_STRING_STATS=
AUTO_LOAD_AUTO_COMMANDS=
AUTO_LOAD_MACRO_COMMANDS=
```

- `LOG_DIR` 미설정 시 연결 시점에 디렉토리 선택 후 `.env`에 자동 저장
- 배포 실행 파일(`dist/lnxterm`) 사용 시 `.env`는 실행 파일 디렉토리를 우선 참조
- `.env`는 git 커밋 금지

## 문서
- 요구사항: `doc/PROMPT.md`
- 구현 계획: `doc/IMPLEMENTATION_PLAN.md`
- 프로젝트 상태: `doc/PROJECT_STATUS.md`
- 워크스루: `doc/WALKTHROUGH.md`
- 세션 인수인계: `doc/HANDOFF.md`

## 라이선스
개인 디버깅 목적 사용을 기준으로 관리 중입니다.
