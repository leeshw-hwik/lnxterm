# LnxTerm 개발 워크스루

## 프로젝트 개요
ST-Link V3 Mini를 이용한 임베디드 장치 디버그/로그 수집용 시리얼 터미널 GUI 프로그램.

## 주요 성과
- **GitHub Release**: [LnxTerm v1.7](https://github.com/leeshw-hwik/lnxterm/releases/tag/v1.7) 배포 완료
- **포트 점유 감지 (v1.7)**: Lockfile + TIOCEXCL 모드로 안정성 강화
- **로그 편의성 (v1.7.2)**: 로그 파일 저장 경로 표시 및 복사 기능 개선
- **단독 배포본**: Python 없이 실행 가능한 Linux 64-bit 바이너리

## 주요 기능 상세

### 포트 점유 감지 (v1.7)
리눅스 시스템 레벨의 점유 상태를 3단계(Lockfile, Process, TIOCEXCL)로 확인하여 충돌을 방지합니다.

### 로그 파일 관리 (v1.7.2)
- 연결 시 자동으로 생성되는 로그 파일의 **절대 경로**를 사이드바에 표시합니다.
- 마우스로 경로를 드래그하여 복사할 수 있어, 터미널에서 `tail -f` 등으로 바로 확인하기 편리합니다.

### 다중 인스턴스
- `./lnxterm &`으로 여러 창을 띄워 각각 다른 포트를 모니터링할 수 있습니다.

## 빌드 및 배포
```bash
./build_exe.sh  # dist/lnxterm 생성
```

## 환경 설정 및 사용법
`README.md`를 참고하세요.

---
본 프로젝트는 **Antigravity AI**에 의해 개발 및 관리되었습니다.
