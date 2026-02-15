# 프로젝트 상태 보고서: LnxTerm

> 현재 버전: **v1.9.1**
> 최종 업데이트: **2026-02-14**
> 타겟 시스템: Linux (ST-Link V3 Mini 디버그 환경)

## 1) 상태 요약
- 자동 명령/문자열 통계 기능 강화 완료
  - UI 시간/개수 표시 개선
  - 자동 명령 설정 범위 확대(24h)
- 빌드(`./build_exe.sh`) 성공, 산출물 `dist/lnxterm` 확인

## 2) 이번 세션 완료 항목
1. **자동 명령 기능 개선**:
   - 시간 설정 범위 확대 (10s -> 24h)
   - 설정 창 타이틀에 명령어 라인 수 표시
   - 목록 UI에 'Last Run' 시간 표시
2. **문자열 통계 UI 개선**:
   - 'Last Detected' 시간 표시 라벨 추가
3. **i18n 개선**:
   - '자동 명령' 그룹 타이틀 간소화 및 번역 키 추가

## 3) 기술/품질 체크
- 문법 검증:
```bash
python3 -m py_compile i18n.py main_window.py sidebar_widget.py search_widget.py automation_dialog.py styles.py
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
1. 실환경에서 언어 전환 후 전체 화면 텍스트 누락 여부 확인
2. 다국어 키 누락 검사 스크립트 추가
3. 자동 명령 고빈도 트리거 성능 테스트
