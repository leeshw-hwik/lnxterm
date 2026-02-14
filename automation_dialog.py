from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, 
    QPushButton, QDialogButtonBox, QSpinBox, QFormLayout, QGroupBox,
    QSizePolicy, QWidget
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from styles import COLORS

class AutomationDialog(QDialog):
    def __init__(self, parent=None, task_data=None):
        super().__init__(parent)
        self.setWindowTitle("자동 명령 설정")
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

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 1. Automatic Command Basic Info
        basic_group = QGroupBox("자동 명령 기본 정보")
        basic_layout = QFormLayout(basic_group)
        basic_layout.setContentsMargins(10, 5, 10, 10) 
        basic_layout.setSpacing(8)
        
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("예: 네트워크 연결")
        basic_layout.addRow("명령 이름:", self._name_input)
        
        self._interval_input = QSpinBox()
        self._interval_input.setRange(0, 10000)
        self._interval_input.setSuffix(" ms")
        self._interval_input.setValue(100)
        self._interval_input.setToolTip("여러 줄의 명령어를 수행할 때, 각 줄 사이의 지연 시간")
        basic_layout.addRow("명령어 간격:", self._interval_input)
        
        layout.addWidget(basic_group)
        
        # 2. Pre-command
        pre_group = QGroupBox("사전 명령 (시작 시 수행)")
        pre_layout = QVBoxLayout(pre_group)
        pre_layout.setContentsMargins(10, 5, 10, 10)
        
        self._pre_cmd_input = QTextEdit()
        self._pre_cmd_input.setPlaceholderText("명령어 입력 (여러 줄 가능)")
        self._pre_cmd_input.setMinimumHeight(60)
        self._pre_cmd_input.setAcceptRichText(False)
        self._pre_cmd_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        pre_layout.addWidget(self._pre_cmd_input)
        
        layout.addWidget(pre_group, 1)
        
        # 3. Trigger Log String (Delay Moved Out)
        trigger_group = QGroupBox("트리거 로그 문자열")
        trigger_layout = QVBoxLayout(trigger_group)
        trigger_layout.setContentsMargins(10, 5, 10, 10)
        
        self._trigger_input = QLineEdit()
        self._trigger_input.setPlaceholderText("감지할 로그 입력")
        trigger_layout.addWidget(self._trigger_input)
        
        layout.addWidget(trigger_group)
        
        # 4. Post-command (Delay Moved In)
        post_group = QGroupBox("사후 명령 (트리거+지연 후 수행)")
        post_layout = QVBoxLayout(post_group)
        post_layout.setContentsMargins(10, 5, 10, 10)
        post_layout.setSpacing(10)
        
        # Delay Input (Moved Here)
        delay_row = QHBoxLayout()
        delay_label = QLabel("감지 후 지연:")
        delay_row.addWidget(delay_label)
        
        self._delay_input = QSpinBox()
        self._delay_input.setRange(0, 3600000) # 1 hour
        self._delay_input.setSuffix(" ms")
        self._delay_input.setValue(100)
        delay_row.addWidget(self._delay_input)
        delay_row.addStretch()
        
        post_layout.addLayout(delay_row)
        
        self._post_cmd_input = QTextEdit()
        self._post_cmd_input.setPlaceholderText("명령어 입력 (여러 줄 가능)")
        self._post_cmd_input.setMinimumHeight(60)
        self._post_cmd_input.setAcceptRichText(False)
        self._post_cmd_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        post_layout.addWidget(self._post_cmd_input)
        
        layout.addWidget(post_group, 2)
        
        # 5. Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        # Cancel Button
        self._cancel_btn = QPushButton(" Cancel")
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
        self._ok_btn = QPushButton(" OK")
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
            "name": self._name_input.text().strip() or "이름 없음",
            "cmd_interval": self._interval_input.value(),
            "pre_cmd": self._pre_cmd_input.toPlainText(),
            "trigger": self._trigger_input.text(),
            "delay": self._delay_input.value(),
            "post_cmd": self._post_cmd_input.toPlainText(),
            "enabled": True  # 기본 활성화
        }
