# LnxTerm (Serial Terminal for Linux)

ST-Link V3 Mini 기반 임베디드 장치 디버깅/로그 수집을 위한 시리얼 터미널 GUI입니다.
현재 배포 기준 버전은 **v1.8.2** 입니다.

## 핵심 기능

- 시리얼 포트 자동 탐색 (`/dev/ttyACM*`, `/dev/ttyUSB*`)
- 연결 끊김 시 자동 재연결 (기본 3초, `.env`로 주기 설정 가능)
- 포트 점유 감지 강화 (Lockfile + `fuser`/`lsof` + `TIOCEXCL`)
- 다중 인스턴스 실행 지원 (포트별 독립 실행)
- 모든 라인 타임스탬프 기록 (`[YYYY-MM-DD HH:MM:SS.mmm]`)
- 로그 파일 자동 생성 및 절대 경로 표시/복사
- 문자열 통계(최대 10개) 카운팅/시작/정지/초기화
- 문자열 통계 CSV 자동 기록
- 열 순서: `문자열, 집계 시점, 누적 카운트, 대소문자 구분, 로그`
- `로그` 열에는 매칭된 원문 1줄 전체 저장
- 터미널 검색 (`Ctrl+F`), 하이라이트, 이전/다음 이동
- One Dark Pro 기반 UI 테마

## v1.8.2 변경 요약

- 실행 환경별 `.env` 참조 경로 개선 (실행 파일 디렉토리 우선)
- 자동 재연결 주기 환경변수화 (`RECONNECT_INTERVAL_MS`, `RECONNECT_INTERVAL_SEC`)
- 로그 파일 세션 고정: 재연결 후 동일 로그 파일 append
- 문자열 통계 CSV 세션 고정: 로그 파일 기반 동일 CSV 유지
- 앱 재시작 없이 연결만 재수립할 때 로그/통계 파일 표시 유지

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

4. 다중 인스턴스 예시

```bash
./lnxterm &
./lnxterm &
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
- 자동 재연결 주기는 `RECONNECT_INTERVAL_MS`(ms) 또는 `RECONNECT_INTERVAL_SEC`(sec)로 설정
- 두 값이 모두 없거나 잘못된 경우 기본값 `3초` 사용
- 배포 실행 파일(`dist/lnxterm`) 사용 시 `.env`는 실행 파일과 같은 디렉토리를 우선 참조
- `.env`는 git에 커밋하지 않음

## 문서

- 요구사항: `doc/PROMPT.MD`
- 구현 계획: `doc/IMPLEMENTATION_PLAN.MD`
- 프로젝트 상태: `doc/PROJECT_STATUS.MD`
- 워크스루: `doc/WALKTHROUGH.MD`

## 릴리스 링크

- v1.8.2: https://github.com/leeshw-hwik/lnxterm/releases/tag/v1.8.2
- v1.8.2 바이너리: https://github.com/leeshw-hwik/lnxterm/releases/download/v1.8.2/lnxterm

## 라이선스

개인 디버깅 목적 사용을 기준으로 관리 중입니다.

---
Created by Antigravity AI
