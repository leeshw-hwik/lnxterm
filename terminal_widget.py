"""
터미널 위젯: 시리얼 데이터 표시, 타임스탬프, 자동 스크롤
"""

from datetime import datetime
from PyQt6.QtWidgets import QPlainTextEdit
from PyQt6.QtGui import QTextCharFormat, QColor, QTextCursor, QFont
from PyQt6.QtCore import Qt, pyqtSignal

from styles import COLORS, get_terminal_stylesheet


class TerminalWidget(QPlainTextEdit):
    """터미널 출력 위젯"""

    DEFAULT_MAX_LINES = 1_000_000

    def __init__(self, parent=None, max_lines: int = None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet(get_terminal_stylesheet())
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setMaximumBlockCount(
            self._normalize_max_lines(max_lines, self.DEFAULT_MAX_LINES)
        )

        # 폰트 설정
        font = QFont("JetBrains Mono", 12)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)

        # 자동 스크롤 상태
        self._auto_scroll = True

        # 미완성 라인 버퍼 (수신 데이터가 줄 단위로 오지 않을 수 있음)
        self._line_buffer = ""

        # 스크롤바 위치 변경 감지
        self.verticalScrollBar().valueChanged.connect(self._on_scroll_changed)
        self.verticalScrollBar().rangeChanged.connect(self._on_range_changed)

    def _normalize_max_lines(self, max_lines: int | None, fallback: int) -> int:
        """최대 라인 수 유효성 검사"""
        if not max_lines:
            return fallback
        try:
            normalized = int(max_lines)
        except (TypeError, ValueError):
            return fallback
        return normalized if normalized > 0 else fallback

    def set_max_lines(self, max_lines: int) -> None:
        """터미널 최대 버퍼 라인 수를 설정"""
        normalized = self._normalize_max_lines(max_lines, self.DEFAULT_MAX_LINES)
        self.setMaximumBlockCount(normalized)

    def _on_scroll_changed(self, value):
        """스크롤 위치 변경 시 자동 스크롤 해제/활성화"""
        scrollbar = self.verticalScrollBar()
        # 최하단 근처면 자동 스크롤 활성화
        self._auto_scroll = (value >= scrollbar.maximum() - 5)

    def _on_range_changed(self, _min, _max):
        """스크롤 범위 변경 시 자동 스크롤"""
        if self._auto_scroll:
            self.verticalScrollBar().setValue(_max)

    @staticmethod
    def get_timestamp() -> str:
        """밀리초 포함 날짜+시간 타임스탬프 반환"""
        now = datetime.now()
        return now.strftime("[%Y-%m-%d %H:%M:%S.") + f"{now.microsecond // 1000:03d}]"

    def append_data(self, data: str, direction: str = "rx") -> list[tuple[str, str]]:
        """수신/송신 데이터를 터미널에 추가

        Args:
            data: 표시할 텍스트
            direction: "rx" (수신), "tx" (송신), "sys" (시스템 메시지)

        Returns:
            완성된 라인 리스트 [(timestamp, line_text), ...]
        """
        completed_lines = []

        # 방향별 색상
        if direction == "tx":
            text_color = QColor(COLORS["terminal_blue"])
        elif direction == "sys":
            text_color = QColor(COLORS["terminal_yellow"])
        else:
            text_color = QColor(COLORS["terminal_green"])

        timestamp_color = QColor(COLORS["terminal_yellow"])

        # 모든 CR 문자 제거 (타임스탬프 덮어쓰기 방지)
        data = data.replace("\r", "")

        # 버퍼에 추가
        self._line_buffer += data

        # 라인 단위로 처리
        while "\n" in self._line_buffer:
            line, self._line_buffer = self._line_buffer.split("\n", 1)

            timestamp = self.get_timestamp()

            # 터미널에 라인 추가 (빈 라인도 타임스탬프와 함께 표시)
            self._append_formatted_line(timestamp, line, timestamp_color, text_color, direction)

            completed_lines.append((timestamp, line))

        return completed_lines

    def _append_formatted_line(
        self, timestamp: str, text: str,
        ts_color: QColor, text_color: QColor,
        direction: str
    ):
        """포맷된 라인을 터미널에 추가"""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # 타임스탬프 포맷
        ts_format = QTextCharFormat()
        ts_format.setForeground(ts_color)

        # 방향 표시 (TX는 접두사 없이 색상만 구분)
        dir_format = QTextCharFormat()
        if direction == "tx":
            dir_format.setForeground(QColor(COLORS["terminal_blue"]))
            dir_prefix = " "
        elif direction == "sys":
            dir_format.setForeground(QColor(COLORS["terminal_yellow"]))
            dir_prefix = " SYS "
        else:
            dir_format.setForeground(QColor(COLORS["terminal_green"]))
            dir_prefix = " "

        # 텍스트 포맷
        txt_format = QTextCharFormat()
        txt_format.setForeground(text_color)

        # 줄 추가
        if self.document().blockCount() > 1 or self.toPlainText():
            cursor.insertText("\n")

        cursor.insertText(timestamp, ts_format)
        cursor.insertText(dir_prefix, dir_format)
        cursor.insertText(text, txt_format)

        self.setTextCursor(cursor)

    def append_system_message(self, message: str) -> list[tuple[str, str]]:
        """시스템 메시지 추가"""
        return self.append_data(message + "\n", direction="sys")

    def flush_buffer(self) -> list[tuple[str, str]]:
        """미완성 라인 버퍼 강제 플러시"""
        completed_lines = []
        if self._line_buffer:
            timestamp = self.get_timestamp()
            full_timestamp = self.get_full_timestamp()
            line = self._line_buffer
            self._line_buffer = ""

            ts_color = QColor(COLORS["terminal_yellow"])
            text_color = QColor(COLORS["terminal_green"])
            self._append_formatted_line(timestamp, line, ts_color, text_color, "rx")

            completed_lines.append((full_timestamp, line))
        return completed_lines

    def clear_terminal(self):
        """터미널 내용 초기화"""
        self.clear()
        self._line_buffer = ""
