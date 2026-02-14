"""
검색 위젯: Ctrl+F 검색, 하이라이트, 이전/다음 이동
"""

from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLineEdit, QLabel, QPushButton
)
from PyQt6.QtGui import QTextCharFormat, QColor, QTextCursor
from PyQt6.QtCore import Qt, pyqtSignal

from styles import COLORS, get_search_widget_stylesheet
from i18n import normalize_language, tr


class SearchWidget(QFrame):
    """검색 바 위젯"""

    closed = pyqtSignal()

    def __init__(self, terminal_widget, parent=None, language: str = "ko"):
        super().__init__(parent)
        self._terminal = terminal_widget
        self._matches = []
        self._current_match_index = -1
        self._language = normalize_language(language)

        self.setObjectName("searchFrame")
        self.setStyleSheet(get_search_widget_stylesheet())
        self.setFixedHeight(40)
        self.setVisible(False)

        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(4)

        # 검색 입력
        self._input = QLineEdit()
        self._input.setObjectName("searchInput")
        self._input.setPlaceholderText(tr(self._language, "search.placeholder"))
        self._input.setMinimumWidth(200)
        self._input.setMaximumWidth(300)
        self._input.textChanged.connect(self._on_search_changed)
        self._input.returnPressed.connect(self.find_next)
        layout.addWidget(self._input)

        # 매치 카운트
        self._match_label = QLabel("")
        self._match_label.setObjectName("matchCount")
        self._match_label.setMinimumWidth(80)
        layout.addWidget(self._match_label)

        # 이전 버튼
        self._prev_btn = QPushButton("▲")
        self._prev_btn.setObjectName("searchNavBtn")
        self._prev_btn.setToolTip(tr(self._language, "search.tooltip.prev"))
        self._prev_btn.clicked.connect(self.find_prev)
        layout.addWidget(self._prev_btn)

        # 다음 버튼
        self._next_btn = QPushButton("▼")
        self._next_btn.setObjectName("searchNavBtn")
        self._next_btn.setToolTip(tr(self._language, "search.tooltip.next"))
        self._next_btn.clicked.connect(self.find_next)
        layout.addWidget(self._next_btn)

        layout.addStretch()

        # 닫기 버튼
        self._close_btn = QPushButton("✕")
        self._close_btn.setObjectName("searchCloseBtn")
        self._close_btn.setToolTip(tr(self._language, "search.tooltip.close"))
        self._close_btn.clicked.connect(self.hide_search)
        layout.addWidget(self._close_btn)

    def set_language(self, language: str):
        self._language = normalize_language(language)
        self._input.setPlaceholderText(tr(self._language, "search.placeholder"))
        self._prev_btn.setToolTip(tr(self._language, "search.tooltip.prev"))
        self._next_btn.setToolTip(tr(self._language, "search.tooltip.next"))
        self._close_btn.setToolTip(tr(self._language, "search.tooltip.close"))
        if self._matches:
            self._update_match_label()
        elif self._input.text():
            self._match_label.setText(tr(self._language, "search.no_results"))

    def show_search(self):
        """검색 바 표시"""
        self.setVisible(True)
        self._input.setFocus()
        self._input.selectAll()

    def hide_search(self):
        """검색 바 숨기기"""
        self.setVisible(False)
        self._clear_highlights()
        self._match_label.setText("")
        self.closed.emit()

    def _on_search_changed(self, text: str):
        """검색어 변경 시"""
        self._clear_highlights()
        self._matches.clear()
        self._current_match_index = -1

        if not text:
            self._match_label.setText("")
            return

        self._find_all(text)
        if self._matches:
            self._current_match_index = 0
            self._highlight_all()
            self._go_to_match(0)
            self._update_match_label()
        else:
            self._match_label.setText(tr(self._language, "search.no_results"))

    def _find_all(self, text: str):
        """모든 매치 찾기"""
        document = self._terminal.document()
        cursor = QTextCursor(document)
        self._matches = []

        while True:
            cursor = document.find(text, cursor)
            if cursor.isNull():
                break
            self._matches.append(cursor)

    def _highlight_all(self):
        """모든 매치 하이라이트"""
        # 일반 매치 하이라이트
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor(COLORS["bg_search"]))
        highlight_format.setForeground(QColor(COLORS["text_primary"]))

        # 현재 매치 하이라이트
        current_format = QTextCharFormat()
        current_format.setBackground(QColor(COLORS["bg_search_current"]))
        current_format.setForeground(QColor(COLORS["text_primary"]))

        # 추가 선택으로 하이라이트 적용
        extra_selections = []
        from PyQt6.QtWidgets import QTextEdit
        for i, cursor in enumerate(self._matches):
            selection = QTextEdit.ExtraSelection()
            if i == self._current_match_index:
                selection.format = current_format
            else:
                selection.format = highlight_format
            selection.cursor = cursor
            extra_selections.append(selection)

        self._terminal.setExtraSelections(extra_selections)

    def _clear_highlights(self):
        """하이라이트 제거"""
        self._terminal.setExtraSelections([])

    def _go_to_match(self, index: int):
        """특정 매치로 이동"""
        if 0 <= index < len(self._matches):
            cursor = self._matches[index]
            self._terminal.setTextCursor(cursor)
            self._terminal.centerCursor()

    def _update_match_label(self):
        """매치 카운트 라벨 업데이트"""
        if self._matches:
            self._match_label.setText(
                f"{self._current_match_index + 1}/{len(self._matches)}"
            )
        else:
            self._match_label.setText(tr(self._language, "search.no_results"))

    def find_next(self):
        """다음 매치로 이동"""
        if not self._matches:
            return
        self._current_match_index = (self._current_match_index + 1) % len(self._matches)
        self._highlight_all()
        self._go_to_match(self._current_match_index)
        self._update_match_label()

    def find_prev(self):
        """이전 매치로 이동"""
        if not self._matches:
            return
        self._current_match_index = (self._current_match_index - 1) % len(self._matches)
        self._highlight_all()
        self._go_to_match(self._current_match_index)
        self._update_match_label()

    def keyPressEvent(self, event):
        """키 이벤트 처리"""
        if event.key() == Qt.Key.Key_Escape:
            self.hide_search()
        elif event.key() == Qt.Key.Key_F3:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.find_prev()
            else:
                self.find_next()
        else:
            super().keyPressEvent(event)
