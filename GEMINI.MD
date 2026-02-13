# LnxTerm 프로젝트 규칙

- 대화 및 문서작성은 한국어를 기본으로 한다.
- `진행시켜` 라는 명령 수행은 `working/hreq.txt` 파일의 내용을 확인하고 수행한다.
- `마무리` 라는 명령 수행은 `doc` 디렉토리 하위의 프로젝트 문서 마크다운 파일들을 모두 최신화하여 업데이트 하고, `working/previous_context.txt` 파일에 현재 세션의 작업을 기록하여 다른 세션에서 이어서 작업 할 수 있도록 정리한다.
- 문서 마크다운 파일은 `doc/` 디렉토리 하위에 저장한다.
- Implementation Plan은 `doc/IMPLEMENTATION_PLAN.MD` 파일에 기록한다.
- AI를 위한 요구사항(Prompt)은 `doc/PROMPT.MD` 파일에 기록한다.
- 개발 진행 상황은 `doc/WALKTHROUGH.MD` 파일에 기록한다.
- 프로젝트 상태 보고서는 `doc/PROJECT_STATUS.MD` 파일에 기록한다.
- `.env` 파일은 절대 AI로 전송하지 않는다 (`.antigravityignore` 등록).
- `.env` 파일은 git에 포함하지 않는다 (`.gitignore` 등록).
