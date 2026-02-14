# LnxTerm 개발 워크스루

## 현재 릴리스
- 버전: **v1.8.4**
- 바이너리: `dist/lnxterm`

## 이번 릴리스 핵심 변경
1. 환경 변수 기반 데이터 로딩: 시작 시 `.env`에서 통계 키워드 및 자동 명령 자동 로드
2. 로딩 모드 지원: ALWAYS, IGNORE, CONFIRM (사용자 선택 가능)
3. 자동 명령 JSON 파싱: 복잡한 자동화 설정을 한 줄의 JSON으로 사전 정의 가능

## 점검 시나리오

### 1) 자동 로딩 확인 (CONFIRM 모드)
1. `.env`에 `AUTO_LOAD_STRING_STATS=TEST1;TEST2` 추가
2. 프로그램 실행 시 "환경 변수에 사전 설정된 데이터가 있습니다... 불러오시겠습니까?" 팝업 확인
3. 'Yes' 선택 시 사이드바 문자열 통계 칸에 TEST1, TEST2가 채워지는지 확인

### 2) 자동 로딩 확인 (ALWAYS 모드)
1. `.env`에 `AUTO_LOAD_MODE=ALWAYS` 설정
2. 재시작 시 팝업 없이 데이터가 즉시 로드되는지 확인

### 3) 자동 명령 로딩 확인
1. `.env`에 `AUTO_LOAD_AUTO_COMMANDS=[{"name":"TestTask","trigger":"OK","post_cmd":"AT","enabled":true}]` 추가
2. 실행 후 사이드바 '자동 명령 정보' 목록에 'TestTask'가 나타나는지 확인

### 4) 자동 저장 및 IGNORE 모드 확인
1. `CONFIRM` 모드로 실행 후 문자열 통계에 'SAVE_TEST' 입력
2. 프로그램 종료 후 `.env` 파일 확인 -> `AUTO_LOAD_STRING_STATS`에 'SAVE_TEST'가 포함되어야 함
3. `.env`에서 `AUTO_LOAD_MODE=IGNORE`로 변경 후 실행
4. 문자열 통계 변경 후 종료 -> `.env` 파일이 변경되지 않아야 함 (업데이트 방지)

## 실행/검증 명령
```bash
./build_exe.sh
./dist/lnxterm
```

## 참고
- `.env.example` 파일을 참조하여 환경 변수를 구성하십시오.
- JSON 파싱 오류 시 터미널(콘솔)에 오류 메시지가 출력됩니다.
