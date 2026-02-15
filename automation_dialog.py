from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, 
    QPushButton, QDialogButtonBox, QSpinBox, QFormLayout, QGroupBox,
    QSizePolicy, QWidget
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from styles import COLORS
from i18n import normalize_language, tr

class AutomationDialog(QDialog):
    def __init__(self, parent=None, task_data=None, language: str = "ko"):
        super().__init__(parent)
        self._language = normalize_language(language)
        self.setWindowTitle(tr(self._language, "automation.title"))
        self.resize(600, 700) 
        self.setMinimumWidth(500)
        self.setMinimumHeight(600)
        
        # 다크 테마 적용
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_dark']};
                color: {COLORS['text_primary']};
            }}
            QLabel {{
                color: {COLORS['text_primary']};
            }}
            QLineEdit, QSpinBox, QTextEdit {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 4px;
            }}
            QLineEdit:focus, QSpinBox:focus, QTextEdit:focus {{
                border: 1px solid {COLORS['border_focus']};
            }}
            QGroupBox {{
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                margin-top: 20px;
                font-weight: bold;
                color: {COLORS['text_secondary']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        
        self._task_data = task_data or {}
        self._setup_ui()
        self._load_data()
        self._apply_language()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 1. Automatic Command Basic Info
        self._basic_group = QGroupBox()
        basic_layout = QFormLayout(self._basic_group)
        basic_layout.setContentsMargins(10, 5, 10, 10) 
        basic_layout.setSpacing(8)
        
        self._name_input = QLineEdit()
        self._name_label = QLabel()
        basic_layout.addRow(self._name_label, self._name_input)
        
        self._interval_input = QSpinBox()
        self._interval_input.setRange(0, 86400000) # 24 hours
        self._interval_input.setSuffix(" ms")
        self._interval_input.setValue(100)
        self._interval_label = QLabel()
        basic_layout.addRow(self._interval_label, self._interval_input)
        
        layout.addWidget(self._basic_group)
        
        # 2. Pre-command
        self._pre_group = QGroupBox()
        pre_layout = QVBoxLayout(self._pre_group)
        pre_layout.setContentsMargins(10, 5, 10, 10)
        
        self._pre_cmd_input = QTextEdit()
        self._pre_cmd_input.setMinimumHeight(60)
        self._pre_cmd_input.setAcceptRichText(False)
        self._pre_cmd_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._pre_cmd_input.textChanged.connect(self._update_pre_title)
        pre_layout.addWidget(self._pre_cmd_input)
        
        layout.addWidget(self._pre_group, 1)
        
        # 3. Trigger Log String (Delay Moved Out)
        self._trigger_group = QGroupBox()
        trigger_layout = QVBoxLayout(self._trigger_group)
        trigger_layout.setContentsMargins(10, 5, 10, 10)
        
        self._trigger_input = QLineEdit()
        trigger_layout.addWidget(self._trigger_input)
        
        layout.addWidget(self._trigger_group)
        
        # 4. Post-command (Delay Moved In)
        self._post_group = QGroupBox()
        post_layout = QVBoxLayout(self._post_group)
        post_layout.setContentsMargins(10, 5, 10, 10)
        post_layout.setSpacing(10)
        
        # Delay Input (Moved Here)
        delay_row = QHBoxLayout()
        self._delay_label = QLabel()
        delay_row.addWidget(self._delay_label)
        
        self._delay_input = QSpinBox()
        self._delay_input.setRange(0, 86400000) # 24 hours
        self._delay_input.setSuffix(" ms")
        self._delay_input.setValue(100)
        delay_row.addWidget(self._delay_input)
        delay_row.addStretch()
        
        post_layout.addLayout(delay_row)
        
        self._post_cmd_input = QTextEdit()
        self._post_cmd_input.setMinimumHeight(60)
        self._post_cmd_input.setAcceptRichText(False)
        self._post_cmd_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._post_cmd_input.textChanged.connect(self._update_post_title)
        post_layout.addWidget(self._post_cmd_input)
        
        layout.addWidget(self._post_group, 2)
        
        # 5. Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        # Cancel Button
        self._cancel_btn = QPushButton()
        self._cancel_btn.setIcon(self._make_icon("x", COLORS['error']))
        self._cancel_btn.setFixedSize(100, 36)
        self._cancel_btn.clicked.connect(self.reject)
        self._cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_input']};
                border-color: {COLORS['error']};
                color: {COLORS['error']};
            }}
        """)
        btn_layout.addWidget(self._cancel_btn)
        
        # OK Button
        self._ok_btn = QPushButton()
        self._ok_btn.setIcon(self._make_icon("check", COLORS['success']))
        self._ok_btn.setFixedSize(100, 36)
        self._ok_btn.clicked.connect(self.accept)
        self._ok_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_input']};
                border-color: {COLORS['success']};
                color: {COLORS['success']};
            }}
        """)
        btn_layout.addWidget(self._ok_btn)
        
        layout.addLayout(btn_layout)

    def set_language(self, language: str):
        self._language = normalize_language(language)
        self._apply_language()

    def _apply_language(self):
        self.setWindowTitle(tr(self._language, "automation.title"))
        self._basic_group.setTitle(tr(self._language, "automation.group.basic"))
        self._update_pre_title()
        self._trigger_group.setTitle(tr(self._language, "automation.group.trigger"))
        self._update_post_title()
        self._name_label.setText(tr(self._language, "automation.label.name"))
        self._interval_label.setText(tr(self._language, "automation.label.interval"))
        self._delay_label.setText(tr(self._language, "automation.label.delay"))
        self._name_input.setPlaceholderText(tr(self._language, "automation.placeholder.name"))
        self._pre_cmd_input.setPlaceholderText(tr(self._language, "automation.placeholder.commands"))
        self._post_cmd_input.setPlaceholderText(tr(self._language, "automation.placeholder.commands"))
        self._trigger_input.setPlaceholderText(tr(self._language, "automation.placeholder.trigger"))
        self._interval_input.setToolTip(tr(self._language, "automation.tooltip.interval"))
        self._cancel_btn.setText(f" {tr(self._language, 'automation.button.cancel')}")
        self._ok_btn.setText(f" {tr(self._language, 'automation.button.ok')}")

    def _update_pre_title(self):
        count = self._get_line_count(self._pre_cmd_input)
        title = tr(self._language, "automation.group.pre")
        if count > 0:
            title += f" ({count})"
        self._pre_group.setTitle(title)

    def _update_post_title(self):
        count = self._get_line_count(self._post_cmd_input)
        title = tr(self._language, "automation.group.post")
        if count > 0:
            title += f" ({count})"
        self._post_group.setTitle(title)

    def _get_line_count(self, text_edit: QTextEdit) -> int:
        text = text_edit.toPlainText().strip()
        if not text:
            return 0
        return len(text.splitlines())

    def _make_icon(self, shape: str, color_hex: str) -> QIcon:
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(0,0,0,0))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        c = QColor(color_hex)
        
        # Pen 설정
        pen = painter.pen()
        pen.setColor(c)
        pen.setWidth(2)
        painter.setPen(pen)
        
        if shape == "check":
            # Simple checkmark
            painter.drawLine(3, 8, 7, 12)
            painter.drawLine(7, 12, 13, 4)
        elif shape == "x":
            # Simple X
            painter.drawLine(4, 4, 12, 12)
            painter.drawLine(12, 4, 4, 12)
            
        painter.end()
        return QIcon(pixmap)

    def _load_data(self):
        if not self._task_data:
            return
            
        self._name_input.setText(self._task_data.get("name", ""))
        self._interval_input.setValue(self._task_data.get("cmd_interval", 100))
        self._pre_cmd_input.setPlainText(self._task_data.get("pre_cmd", ""))
        self._trigger_input.setText(self._task_data.get("trigger", ""))
        self._delay_input.setValue(self._task_data.get("delay", 100))
        self._post_cmd_input.setPlainText(self._task_data.get("post_cmd", ""))

    def get_data(self):
        return {
            "name": self._name_input.text().strip() or tr(self._language, "automation.default_name"),
            "cmd_interval": self._interval_input.value(),
            "pre_cmd": self._pre_cmd_input.toPlainText(),
            "trigger": self._trigger_input.text(),
            "delay": self._delay_input.value(),
            "post_cmd": self._post_cmd_input.toPlainText(),
            "enabled": True  # 기본 활성화
        }
