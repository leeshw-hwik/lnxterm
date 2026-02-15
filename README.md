# LnxTerm (Serial Terminal for Linux)

ST-Link V3 Mini 기반 임베디드 장치 디버깅/로그 수집용 시리얼 터미널 GUI입니다.
- 현재 작업 기준 버전: **v1.9.1**

## 핵심 기능

- 시리얼 포트 자동 탐색 (`/dev/ttyACM*`, `/dev/ttyUSB*`)
- 포트 점유 감지 (Lockfile + `fuser`/`lsof` + `TIOCEXCL`)
- 연결 끊김 시 자동 재연결 (기본 3초, `.env` 설정 가능)
- 로그 파일 자동 생성 및 절대 경로 표시/복사
- 문자열 통계(최대 10개) 카운팅/시작/정지/초기화 (**Last Detected 시간 표시**)
- 문자열 통계 CSV 자동 기록
- 자동 명령(트리거/지연/명령 간격, **최대 24시간 설정, Last Run 시간 표시**)
- 터미널 검색 (`Ctrl+F`), 하이라이트, 이전/다음 이동
- 다국어 지원(한국어/English) + 메뉴에서 언어 전환 가능
- 첫 실행 기본 언어 English (`QSettings` 미존재 시)
- 메뉴 하이라이트를 VS Code Dark 계열 대비로 개선

## v1.9.0 변경 요약

1. 자동 명령 설정 강화
- 지연/간격 시간 설정 한계를 10초에서 24시간으로 대폭 확대
- 명령어 입력 창 타이틀에 라인 수 표시 기능 추가
- 목록 UI에 마지막 실행 시간(Last Run) 표시

2. 문자열 통계 정보 추가
- 통계 UI에 마지막 검출 시간(Last Detected) 표시 라벨 추가

3. UI/UX 개선
- 자동 명령 목록 아이템 레이아웃 개선 (정보 가독성 향상)
- 다국어 텍스트 일부 수정 ('자동 명령 정보' -> '자동 명령')

2. 사용자 언어 설정 저장
- `QSettings` 기반 언어 저장/복원
- 메뉴 `Language`에서 `한국어/English` 전환

3. 기본 언어 정책 변경
- 첫 실행 기본값을 한국어에서 영어로 변경

4. 메뉴 가독성 개선
- 메뉴 선택/하이라이트 색상 대비를 VS Code Dark 스타일로 조정

## 빠른 실행 (릴리스 바이너리)

1. [Releases](https://github.com/leeshw-hwik/lnxterm/releases)에서 최신 `lnxterm` 다운로드
2. 실행 권한 부여

```bash
chmod +x lnxterm
```

3. 실행

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
RECONNECT_INTERVAL_MS=3000
# RECONNECT_INTERVAL_SEC=3
```

- `LOG_DIR` 미설정 시 실행 중 디렉토리 선택 후 `.env`에 저장
- 자동 재연결 주기는 `RECONNECT_INTERVAL_MS`(ms) 또는 `RECONNECT_INTERVAL_SEC`(sec) 사용
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
