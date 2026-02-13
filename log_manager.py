"""
로그 파일 관리 모듈
- 밀리초 타임스탬프 포함 라인 단위 로그 기록
- 덮어쓰기(overwrite) / 추가(append) 모드 지원
"""

import os
from datetime import datetime


class LogManager:
    """로그 파일 관리 클래스"""

    MODE_APPEND = "a"
    MODE_OVERWRITE = "w"

    def __init__(self):
        self._file = None
        self._file_path: str = ""
        self._is_logging: bool = False
        self._mode: str = self.MODE_APPEND
        self._started_at: str = ""

    @staticmethod
    def get_timestamp() -> str:
        """밀리초 포함 타임스탬프 문자열 반환"""
        now = datetime.now()
        return now.strftime("[%Y-%m-%d %H:%M:%S.") + f"{now.microsecond // 1000:03d}]"

    def start_logging(self, file_path: str, mode: str = None) -> None:
        """로그 기록 시작

        Args:
            file_path: 로그 파일 경로
            mode: "a" (추가) 또는 "w" (덮어쓰기), None이면 현재 설정 유지
        """
        if self._is_logging:
            self.stop_logging()

        if mode is not None:
            self._mode = mode

        # 디렉토리가 없으면 생성
        dir_path = os.path.dirname(file_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)

        self._file_path = file_path
        self._file = open(file_path, self._mode, encoding="utf-8")
        self._is_logging = True
        self._started_at = self.get_timestamp()

        # 로그 시작 헤더
        header = f"{self._started_at} === 로그 기록 시작 ==="
        self._file.write(header + "\n")
        self._file.flush()

    def stop_logging(self) -> None:
        """로그 기록 중지"""
        if self._file and not self._file.closed:
            footer = f"{self.get_timestamp()} === 로그 기록 종료 ==="
            self._file.write(footer + "\n")
            self._file.flush()
            self._file.close()
        self._file = None
        self._is_logging = False
        self._started_at = ""

    def write_line(self, line: str, timestamp: str = None) -> None:
        """타임스탬프 포함 한 라인 기록

        Args:
            line: 기록할 텍스트
            timestamp: 타임스탬프 (None이면 현재 시각)
        """
        if not self._is_logging or not self._file:
            return

        if timestamp is None:
            timestamp = self.get_timestamp()

        self._file.write(f"{timestamp} {line}\n")
        self._file.flush()

    @property
    def is_logging(self) -> bool:
        return self._is_logging

    @property
    def file_path(self) -> str:
        return self._file_path

    @property
    def mode(self) -> str:
        return self._mode

    @mode.setter
    def mode(self, value: str):
        if value in (self.MODE_APPEND, self.MODE_OVERWRITE):
            self._mode = value

    @property
    def started_at(self) -> str:
        return self._started_at

    def __del__(self):
        """소멸자: 열린 파일 닫기"""
        if self._is_logging:
            self.stop_logging()
