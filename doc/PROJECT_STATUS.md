# 프로젝트 상태 보고서: LnxTerm

> 현재 버전: **v1.8.5**
> 최종 업데이트: **2026-02-14**
> 타겟 시스템: Linux (ST-Link V3 Mini 디버그 환경)

## 1) 상태 요약
- 다국어(한국어/영어) UI 반영 완료
- 사용자 언어 전환/저장(`QSettings`) 완료
- 첫 실행 기본 언어를 영어로 변경 완료
- 메뉴 하이라이트 가독성(VS Code Dark 계열) 보정 완료
- 빌드(`./build_exe.sh`) 성공, 산출물 `dist/lnxterm` 확인

## 2) 이번 세션 완료 항목
1. `i18n.py` 추가 및 공통 번역 구조 도입
2. `MainWindow` 메뉴/메시지/상태 텍스트 다국어화
3. `SidebarWidget`/`SearchWidget`/`AutomationDialog` 다국어화
4. 메뉴 `Language` 항목 추가 및 런타임 전환 적용
5. 스타일시트 메뉴 선택 상태 대비 개선

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
