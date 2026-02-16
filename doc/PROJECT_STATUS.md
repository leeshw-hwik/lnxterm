# 프로젝트 상태 보고서: LnxTerm

> 현재 버전: **v1.10.0**
> 최종 업데이트: **2026-02-16**
> 타겟 시스템: Linux (ST-Link V3 Mini 디버그 환경)

## 1) 상태 요약
- `v1.10.0` 반영 완료
- 핵심 변경:
  - `.env` 자동 생성 및 변경 즉시 저장
  - 자동 명령/문자열 통계 실행 조건 강화
  - 자동 명령 즉시 중지 및 `sleep(ms)` 처리
  - 매크로 등록/실행 기능 추가
  - 활성 창 복귀 시 명령 입력 포커스 자동 복원
- 빌드(`./build_exe.sh`) 성공, 산출물 `dist/lnxterm` 확인

## 2) 이번 세션 완료 항목
1. **환경변수 체계 개선**
   - `.env` 미존재 시 자동 생성
   - 초기 기본값: `RECONNECT_INTERVAL_MS=1000`
   - 통계/자동 명령/매크로 변경 시 즉시 `.env` 반영
2. **자동 명령 안정화**
   - 시작 시 자동 활성화 방지
   - 미연결 상태 시작 차단
   - `Stop` 시 예약 실행 즉시 취소
   - `sleep(ms)` 지연 명령 지원
3. **문자열 통계 정책 강화**
   - 미연결 상태 시작 차단
4. **매크로 기능 추가**
   - 최대 1000개 등록, 설명 200자 제한
   - 번호 클릭 즉시 전송
   - 단축키 10개 제공(`Ctrl+1~9`, `Ctrl+0`)

## 3) 기술/품질 체크
- 문법 검증:
```bash
python3 -m py_compile main.py main_window.py sidebar_widget.py macro_dialog.py automation_dialog.py i18n.py
```
- 빌드:
```bash
./build_exe.sh
```

## 4) Known Issues
- PyInstaller 빌드 경고 가능:
  - `libxcb-cursor.so.0`
  - `libtiff.so.5`
- 경고가 있어도 빌드 산출물 생성은 정상일 수 있음.
- 타겟 환경에서 의존성 설치 여부 최종 확인 필요.

## 5) 다음 우선순위
1. 매크로/자동 명령 장시간 운용(지연/중지) 실기기 회귀 테스트
2. 자동 명령 타이머 로직 단위 테스트 추가
3. `sidebar_widget.py` 책임 분리 리팩토링
