from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from i18n import normalize_language, tr
from styles import COLORS


class MacroDialog(QDialog):
    """자주 쓰는 명령어(매크로) 등록/실행 창."""

    send_requested = pyqtSignal(str)
    commands_changed = pyqtSignal(list)

    MAX_COMMANDS = 1000

    def __init__(self, parent=None, language: str = "ko"):
        super().__init__(parent)
        self._language = normalize_language(language)
        self._suppress_item_changed = False
        self._shortcut_list = []
        self._setup_ui()
        self._setup_shortcuts()
        self._apply_language()

    def _setup_ui(self):
        self.resize(920, 520)
        self.setStyleSheet(
            f"""
            QDialog {{
                background-color: {COLORS['bg_dark']};
                color: {COLORS['text_primary']};
            }}
            QLabel {{
                color: {COLORS['text_primary']};
            }}
            QTableWidget {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                gridline-color: {COLORS['border']};
            }}
            """
        )

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(8)

        self._shortcut_label = QLabel()
        self._shortcut_label.setWordWrap(True)
        root_layout.addWidget(self._shortcut_label)

        action_row = QHBoxLayout()
        action_row.setContentsMargins(0, 0, 0, 0)
        action_row.setSpacing(6)

        self._add_btn = QPushButton()
        self._add_btn.clicked.connect(self._add_row)
        action_row.addWidget(self._add_btn)

        self._delete_btn = QPushButton()
        self._delete_btn.clicked.connect(self._delete_selected_rows)
        action_row.addWidget(self._delete_btn)
        action_row.addStretch()
        root_layout.addLayout(action_row)

        self._table = QTableWidget(0, 3, self)
        self._table.setHorizontalHeaderLabels(["#", "", ""])
        self._table.setAlternatingRowColors(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
        )
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setColumnWidth(0, 56)
        self._table.setColumnWidth(1, 280)
        self._table.itemChanged.connect(self._on_item_changed)
        self._table.cellClicked.connect(self._on_cell_clicked)
        root_layout.addWidget(self._table, 1)

    def _setup_shortcuts(self):
        # 1~9, 0(10번)만 제공
        for idx in range(1, 10):
            shortcut = QShortcut(QKeySequence(f"Ctrl+{idx}"), self)
            shortcut.activated.connect(lambda i=idx - 1: self._send_row(i))
            self._shortcut_list.append(shortcut)

        shortcut_ten = QShortcut(QKeySequence("Ctrl+0"), self)
        shortcut_ten.activated.connect(lambda: self._send_row(9))
        self._shortcut_list.append(shortcut_ten)

    def set_language(self, language: str):
        self._language = normalize_language(language)
        self._apply_language()

    def _apply_language(self):
        self.setWindowTitle(tr(self._language, "macro.title"))
        self._shortcut_label.setText(tr(self._language, "macro.label.shortcuts"))
        self._add_btn.setText(tr(self._language, "macro.button.add"))
        self._delete_btn.setText(tr(self._language, "macro.button.delete"))
        self._table.setHorizontalHeaderLabels(
            [
                tr(self._language, "macro.table.no"),
                tr(self._language, "macro.table.command"),
                tr(self._language, "macro.table.description"),
            ]
        )

    def set_commands(self, commands):
        self._suppress_item_changed = True
        self._table.setRowCount(0)
        for item in commands[: self.MAX_COMMANDS]:
            command = str(item.get("command", "")).strip()
            description = str(item.get("description", "")).strip()[:200]
            self._append_row(command, description, emit_change=False)
        self._suppress_item_changed = False

    def get_commands(self):
        commands = []
        for row in range(self._table.rowCount()):
            command = self._get_cell_text(row, 1)
            description = self._get_cell_text(row, 2)[:200]
            if not command and not description:
                continue
            commands.append({"command": command, "description": description})
        return commands

    def _append_row(self, command: str = "", description: str = "", emit_change: bool = True):
        row = self._table.rowCount()
        if row >= self.MAX_COMMANDS:
            QMessageBox.warning(
                self,
                tr(self._language, "macro.dialog.max.title"),
                tr(self._language, "macro.dialog.max.body", max_count=self.MAX_COMMANDS),
            )
            return

        self._table.insertRow(row)

        number_item = QTableWidgetItem(str(row + 1))
        number_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        number_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        number_item.setToolTip(tr(self._language, "macro.tooltip.send_on_number"))
        self._table.setItem(row, 0, number_item)

        command_item = QTableWidgetItem(command)
        command_item.setToolTip(command)
        self._table.setItem(row, 1, command_item)

        desc_item = QTableWidgetItem(description[:200])
        self._table.setItem(row, 2, desc_item)

        if emit_change:
            self._emit_commands_changed()

    def _add_row(self):
        self._append_row()

    def _delete_selected_rows(self):
        selected_rows = sorted(
            {item.row() for item in self._table.selectedItems()},
            reverse=True,
        )
        if not selected_rows:
            return

        for row in selected_rows:
            self._table.removeRow(row)
        self._renumber_rows()
        self._emit_commands_changed()

    def _renumber_rows(self):
        self._suppress_item_changed = True
        for row in range(self._table.rowCount()):
            number_item = self._table.item(row, 0)
            if number_item is None:
                number_item = QTableWidgetItem()
                number_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                self._table.setItem(row, 0, number_item)
            number_item.setText(str(row + 1))
            number_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            number_item.setToolTip(tr(self._language, "macro.tooltip.send_on_number"))
        self._suppress_item_changed = False

    def _on_item_changed(self, item: QTableWidgetItem):
        if self._suppress_item_changed:
            return
        if item.column() == 1:
            item.setToolTip(item.text().strip())
        if item.column() == 2 and len(item.text()) > 200:
            self._suppress_item_changed = True
            item.setText(item.text()[:200])
            self._suppress_item_changed = False
        self._emit_commands_changed()

    def _on_cell_clicked(self, row: int, column: int):
        # 번호 셀 클릭 시 즉시 전송
        if column == 0:
            self._send_row(row)

    def _send_row(self, row: int):
        if row < 0 or row >= self._table.rowCount():
            return
        command = self._get_cell_text(row, 1)
        if not command:
            return
        self.send_requested.emit(command)

    def _emit_commands_changed(self):
        self._renumber_rows()
        self.commands_changed.emit(self.get_commands())

    def _get_cell_text(self, row: int, col: int) -> str:
        item = self._table.item(row, col)
        if item is None:
            return ""
        return item.text().strip()
