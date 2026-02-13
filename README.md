# LnxTerm (Serial Terminal Application)

ST-Link V3 Mini를 통한 임베디드 장치 디버그 및 로그 수집을 위한 전용 시리얼 터미널 GUI 프로그램입니다. VS Code Dark+ 스타일의 현대적인 디자인과 편리한 부가 기능을 제공합니다.

## 주요 특징

- **현대적인 UI**: VS Code Dark+ 테마를 적용하여 가독성이 높고 익숙한 개발 환경을 제공합니다.
- **스마트 타임스탬프**: 모든 라인(빈 라인 포함)에 `[YYYY-MM-DD HH:MM:SS.mmm]` 형식의 정밀한 타임스탬프를 부여합니다.
- **자동 재연결**: 연결이 끊겼을 때 3초마다 자동으로 재시도를 수행하여 디버깅 흐름을 끊지 않습니다.
- **자동 로깅**: 기기 연결 시 `.env`에 설정된 경로로 타임스탬프가 포함된 로그 파일(`lnxterm_YYYYMMDD_HHMMSS.log`)을 즉시 생성하여 기록합니다.
- **강력한 검색**: `Ctrl+F`를 통해 터미널 내용 내 실시간 검색 및 이동이 가능합니다.
- **보안 중심**: 중요 설정(.env)이 외부로 유출되지 않도록 설계 및 관리됩니다.

## 스크린샷

*(이미지 준비 중)*

## 설치 및 실행 방법

### 요구 사항
- Python 3.8 이상
- Linux (지원 OS)

### 실행 방법
저장소를 클론한 후, 포함된 `run.sh` 스크립트를 사용하여 가상 환경 구축 및 앱 실행을 한 번에 처리할 수 있습니다.

```bash
# 실행 권한 부여
chmod +x run.sh

# 앱 실행
./run.sh
```

또는 수동으로 가상 환경을 구축할 수 있습니다:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

## 환경 설정 (.env)

프로그램 실행 시 로그 디렉토리가 설정되지 않았다면 선택 창이 나타납니다. 설정된 경로는 `.env` 파일에 기록됩니다.

```env
LOG_DIR=/your/custom/log/path
```

## 라이선스

이 프로젝트는 개인 디버깅 목적으로 제작되었으며, 협의 없이 상업적 이용을 금합니다.

---
Created by Antigravity AI
