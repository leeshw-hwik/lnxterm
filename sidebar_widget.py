"""
사이드바 위젯: 포트 설정, 연결 제어, 로그 파일
"""

import csv
import serial.tools.list_ports
import os
from datetime import datetime
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QGroupBox, QGridLayout, QLineEdit, QScrollArea, QStyle,
    QApplication, QMessageBox,
    QCheckBox,
    QWidget, QSizePolicy, QTextEdit, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QIntValidator, QPainter, QPixmap, QIcon, QColor, QFont, QCursor

from serial_manager import SerialManager
from styles import COLORS
from automation_dialog import AutomationDialog


class SidebarWidget(QFrame):
    """사이드바 패널 위젯"""

    MAX_LOG_COUNTERS = 10
    MAX_AUTO_TASKS = 10

    # 시그널
    connect_requested = pyqtSignal(dict)    # 연결 요청 (설정 딕셔너리)
    disconnect_requested = pyqtSignal()     # 연결 해제 요청
    log_stop_requested = pyqtSignal()       # 로그 중지
    clear_requested = pyqtSignal()          # 터미널 클리어
    send_command_requested = pyqtSignal(str, int) # 명령 전송 요청 (명령어, 간격ms)

    def __init__(self, parent=None):
# ... (rest of init same)
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setMinimumWidth(240)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        self._is_connected = False
        self._is_logging = False
        self._log_counters = []
        self._stats_csv_path = ""
        
        # 자동화 관련 상태
        # Task Dict Structure:
        # { "name": str, "pre_cmd": str, "trigger": str, "post_cmd": str, 
        #   "delay": int, "cmd_interval": int, "enabled": bool, "running": bool }
        self._automation_tasks = [] 

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # === 상단 빠른 도구 버튼 ===
        action_row = QWidget()
        action_layout = QHBoxLayout(action_row)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(6)

        self._connect_btn = QPushButton()
        self._connect_btn.setFixedSize(34, 34)
        self._connect_btn.setIconSize(QSize(20, 20))
        self._connect_btn.setToolTip("연결")
        self._connect_btn.setIcon(
            self._make_power_icon(is_on=True, size=20)
        )
        self._connect_btn.clicked.connect(self._on_connect_clicked)
        action_layout.addWidget(self._connect_btn)

        self._clear_btn = QPushButton()
        self._clear_btn.setObjectName("secondaryBtn")
        self._clear_btn.setFixedSize(34, 34)
        self._clear_btn.setIconSize(QSize(22, 22))
        self._clear_btn.setToolTip("터미널 클리어")
        self._clear_btn.setIcon(self._make_broom_icon(size=22))
        self._clear_btn.clicked.connect(self.clear_requested.emit)
        action_layout.addWidget(self._clear_btn)
        # 자동 명령 설정 버튼 (New)
        self._auto_btn = QPushButton()
        self._auto_btn.setObjectName("secondaryBtn")
        self._auto_btn.setFixedSize(34, 34)
        self._auto_btn.setIconSize(QSize(16, 16))
        self._auto_btn.setToolTip("자동 명령 추가/관리")
        self._auto_btn.setIcon(self._make_robot_icon())
        self._auto_btn.clicked.connect(self._add_automation_task)
        action_layout.addWidget(self._auto_btn)

        action_layout.addStretch()

        layout.addWidget(action_row)

        # === 연결 설정 섹션 (접이식) ===
        self._conn_toggle_btn = QPushButton("연결 설정 ▼")
        self._conn_toggle_btn.setCheckable(True)
        self._conn_toggle_btn.setChecked(True)
        self._conn_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._conn_toggle_btn.setStyleSheet(f"""
            QPushButton {{
                text-align: left;
                font-weight: bold;
                border: 1px solid {COLORS['border']};
                padding: 6px 10px;
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_hover']};
            }}
            QPushButton:checked {{
                background-color: {COLORS['bg_input']};
                border-bottom-left-radius: 0;
                border-bottom-right-radius: 0;
            }}
        """)
        self._conn_toggle_btn.toggled.connect(self._on_conn_toggle)
        layout.addWidget(self._conn_toggle_btn)

        self._conn_content_widget = QWidget()
        self._conn_content_widget.setObjectName("connContent")
        self._conn_content_widget.setStyleSheet(f"""
            #connContent {{
                border: 1px solid {COLORS['border']};
                border-top: none;
                border-bottom-left-radius: 4px;
                border-bottom-right-radius: 4px;
                background-color: transparent;
            }}
        """)
        
        # Grid Layout for Content
        conn_layout = QGridLayout(self._conn_content_widget)
        conn_layout.setHorizontalSpacing(8)
        conn_layout.setVerticalSpacing(12)
        conn_layout.setContentsMargins(10, 10, 10, 10)
        conn_layout.setColumnStretch(0, 0)
        conn_layout.setColumnStretch(1, 1)

        def add_conn_row(row: int, label_text: str, widget: QWidget):
            label = QLabel(label_text)
            label.setMinimumWidth(56)
            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            conn_layout.addWidget(label, row, 0)
            conn_layout.addWidget(widget, row, 1)

        # 포트 선택
        port_row = QHBoxLayout()
        port_row.setContentsMargins(0, 0, 0, 0)
        port_row.setSpacing(4)
        self._port_combo = QComboBox()
        self._port_combo.setMinimumWidth(120)
        self._port_combo.setFixedHeight(32)
        port_row.addWidget(self._port_combo, 1)

        self._refresh_btn = QPushButton()
        self._refresh_btn.setObjectName("secondaryBtn")
        self._refresh_btn.setFixedSize(32, 32)
        self._refresh_btn.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload)
        )
        self._refresh_btn.setIconSize(QSize(16, 16))
        self._refresh_btn.setToolTip("포트 새로고침")
        self._refresh_btn.clicked.connect(self.refresh_ports)
        port_row.addWidget(self._refresh_btn)

        # Port Row (Direct Layout)
        port_label = QLabel("Port:")
        port_label.setMinimumWidth(56)
        port_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        conn_layout.addWidget(port_label, 0, 0)
        conn_layout.addLayout(port_row, 0, 1)

        # Baudrate 선택
        self._baud_combo = QComboBox()
        for rate in SerialManager.BAUDRATES:
            self._baud_combo.addItem(str(rate), rate)
        self._baud_combo.setFixedHeight(32)
        # 기본값 115200
        idx = self._baud_combo.findData(SerialManager.DEFAULT_BAUDRATE)
        if idx >= 0:
            self._baud_combo.setCurrentIndex(idx)
        add_conn_row(1, "Baud:", self._baud_combo)

        # Data Bits
        self._data_combo = QComboBox()
        for label, value in SerialManager.DATABITS.items():
            self._data_combo.addItem(label, value)
        self._data_combo.setFixedHeight(32)
        self._data_combo.setCurrentIndex(3)  # 8 bits
        add_conn_row(2, "Data:", self._data_combo)

        # Parity
        self._parity_combo = QComboBox()
        for label, value in SerialManager.PARITIES.items():
            self._parity_combo.addItem(label, value)
        self._parity_combo.setFixedHeight(32)
        add_conn_row(3, "Parity:", self._parity_combo)

        # Stop Bits
        self._stop_combo = QComboBox()
        for label, value in SerialManager.STOPBITS.items():
            self._stop_combo.addItem(label, value)
        self._stop_combo.setFixedHeight(32)
        add_conn_row(4, "Stop:", self._stop_combo)

        # 터미널 최대 라인 수
        self._max_lines_input = QLineEdit()
        self._max_lines_input.setPlaceholderText("1000000")
        self._max_lines_input.setText("1000000")
        self._max_lines_input.setFixedHeight(32)
        self._max_lines_input.setValidator(QIntValidator(1, 5_000_000, self))
        add_conn_row(5, "Buffer:", self._max_lines_input)

        layout.addWidget(self._conn_content_widget)

        # === 로그 정보 섹션 ===
        log_group = QGroupBox("로그 파일")
        log_group.setObjectName("logGroup")
        log_layout = QVBoxLayout(log_group)
        log_layout.setSpacing(8)
        log_layout.setContentsMargins(10, 4, 10, 10)

        # 로깅 시작 시간 표시
        self._log_started_label = QLabel("로깅 시작 시간: -")
        self._log_started_label.setStyleSheet(
            f"background-color: transparent; color: {COLORS['text_secondary']}; font-size: 11px;"
        )
        self._log_started_label.setWordWrap(True)
        log_layout.addWidget(self._log_started_label)

        # 현재 로그 파일 표시
        log_path_row = QWidget()
        log_path_row_layout = QHBoxLayout(log_path_row)
        log_path_row_layout.setContentsMargins(0, 0, 0, 0)
        log_path_row_layout.setSpacing(4)
        log_path_row_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._log_copy_btn = QPushButton()
        self._log_copy_btn.setObjectName("copyBtn")
        self._log_copy_btn.setFixedSize(20, 9)
        self._log_copy_btn.setIconSize(QSize(8, 5))
        self._log_copy_btn.setToolTip("로그 파일 경로 복사")
        self._log_copy_btn.setIcon(self._make_copy_icon(7))
        self._log_copy_btn.setEnabled(False)
        self._log_copy_btn.clicked.connect(self._copy_log_path)
        log_path_row_layout.addWidget(self._log_copy_btn, 0, Qt.AlignmentFlag.AlignTop)

        self._log_actual_label = QLabel("-")
        self._log_actual_label.setStyleSheet(
            f"background-color: transparent; color: {COLORS['text_secondary']}; font-size: 11px;"
        )
        self._log_actual_label.setWordWrap(True)
        self._log_actual_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        self._log_actual_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._log_actual_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        log_path_row_layout.addWidget(self._log_actual_label, 1, Qt.AlignmentFlag.AlignTop)
        log_layout.addWidget(log_path_row)

        layout.addWidget(log_group)

        # === 문자열 찾기 섹션 ===
        find_group = QGroupBox("문자열 통계")
        find_layout = QVBoxLayout(find_group)
        find_layout.setSpacing(4)
        find_layout.setContentsMargins(10, 4, 10, 4)

        self._stats_file_label = QLabel("-")
        self._stats_file_label.setWordWrap(True)
        self._stats_file_label.setStyleSheet(
            f"background-color: transparent; color: {COLORS['text_secondary']}; font-size: 11px;"
        )
        self._stats_file_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._stats_file_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        stats_file_row = QWidget()
        stats_file_row_layout = QHBoxLayout(stats_file_row)
        stats_file_row_layout.setContentsMargins(0, 0, 0, 0)
        stats_file_row_layout.setSpacing(4)
        stats_file_row_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._stats_copy_btn = QPushButton()
        self._stats_copy_btn.setObjectName("copyBtn")
        self._stats_copy_btn.setFixedSize(20, 9)
        self._stats_copy_btn.setIconSize(QSize(8, 5))
        self._stats_copy_btn.setToolTip("통계 파일 경로 복사")
        self._stats_copy_btn.setIcon(self._make_copy_icon(7))
        self._stats_copy_btn.setEnabled(False)
        self._stats_copy_btn.clicked.connect(self._copy_stats_path)
        stats_file_row_layout.addWidget(self._stats_copy_btn, 0, Qt.AlignmentFlag.AlignTop)
        stats_file_row_layout.addWidget(self._stats_file_label, 1, Qt.AlignmentFlag.AlignTop)
        find_layout.addWidget(stats_file_row)

        case_row = QWidget()
        case_row_layout = QHBoxLayout(case_row)
        case_row_layout.setContentsMargins(0, 0, 0, 0)
        case_row_layout.setSpacing(4)

        self._case_sensitive_checkbox = QCheckBox("대소문자 구분")
        self._case_sensitive_checkbox.setChecked(False)
        self._case_sensitive_checkbox.setMinimumHeight(24)
        case_row_layout.addWidget(self._case_sensitive_checkbox, 1)

        self._reset_all_btn = QPushButton("전체 초기화")
        self._reset_all_btn.setObjectName("secondaryBtn")
        self._reset_all_btn.setFixedHeight(20)
        self._reset_all_btn.setMinimumWidth(82)
        self._reset_all_btn.setToolTip("문자열 통계 전체 항목 초기화")
        # Override min-height from styles.py to allow 20px
        self._reset_all_btn.setStyleSheet("QPushButton { min-height: 0px; margin: 0px; padding: 2px; }")
        self._reset_all_btn.clicked.connect(self._reset_all_log_counters)
        case_row_layout.addWidget(self._reset_all_btn)

        find_layout.addWidget(case_row)

        # 문자열 찾기 입력 목록 (최대 10개)
        counter_scroll = QScrollArea()
        counter_scroll.setFrameShape(QFrame.Shape.NoFrame)
        counter_scroll.setWidgetResizable(True)
        counter_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        counter_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        counter_container = QWidget()
        counter_layout = QVBoxLayout(counter_container)
        counter_layout.setContentsMargins(0, 0, 0, 0)
        counter_layout.setSpacing(4)

        for index in range(self.MAX_LOG_COUNTERS):
            item_frame = QFrame()
            item_frame.setStyleSheet(
                f"QFrame {{ border: 1px solid {COLORS['border']}; border-radius: 4px; background-color: transparent; }}"
            )
            item_layout = QVBoxLayout(item_frame)
            item_layout.setContentsMargins(8, 8, 8, 8)
            item_layout.setSpacing(6)

            # 1. Input Row
            text_input = QLineEdit()
            text_input.setPlaceholderText(f"문자열 {index + 1}")
            text_input.setMinimumHeight(28)
            text_input.textChanged.connect(
                lambda _text, idx=index: self._on_log_keyword_changed(idx)
            )
            item_layout.addWidget(text_input)

            # 2. Bottom Row (Left: Info, Right: Actions)
            bottom_row = QHBoxLayout()
            bottom_row.setContentsMargins(0, 0, 0, 0)
            bottom_row.setSpacing(4)
            
            # Left: Info (Count / Start Time)
            info_layout = QVBoxLayout()
            info_layout.setContentsMargins(0, 0, 0, 0)
            info_layout.setSpacing(2)
            
            count_label = QLabel("Count: 0")
            count_label.setStyleSheet(f"color: {COLORS['text_disabled']}; font-size: 11px; font-weight: bold; background-color: transparent; border: none;")
            info_layout.addWidget(count_label)
            
            started_at_label = QLabel("Start: -")
            started_at_label.setStyleSheet(f"color: {COLORS['text_disabled']}; font-size: 11px; background-color: transparent; border: none;")
            info_layout.addWidget(started_at_label)
            
            bottom_row.addLayout(info_layout)
            bottom_row.addStretch()

            # Right: Actions (Status, Toggle, Reset)
            action_layout = QHBoxLayout()
            action_layout.setContentsMargins(0, 0, 0, 0)
            action_layout.setSpacing(6)
            
            # Status
            status_label = QLabel("OFF")
            status_label.setStyleSheet(f"color: {COLORS['error']}; font-weight: bold; font-size: 11px; border: none;")
            status_label.setAlignment(Qt.AlignmentFlag.AlignVCenter) # removed right align for tighter packing
            action_layout.addWidget(status_label)
            
            # Toggle Button (Start/Stop) - Same as Automation Info (padding 2px 8px)
            toggle_btn = QPushButton("Start")
            toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            toggle_btn.setFixedSize(50, 24)
            # Style set in update_ui, initial style here
            toggle_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {COLORS['success']};
                    border: 1px solid {COLORS['success']};
                    border-radius: 3px;
                    padding: 2px 8px;
                    font-size: 11px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['success']};
                    color: #FFFFFF;
                }}
            """)
            toggle_btn.clicked.connect(lambda _, idx=index: self._toggle_log_counter(idx))
            action_layout.addWidget(toggle_btn)
            
            # Reset Button - Height same as Toggle, Width maintained (24 -> maybe fit content or fixed?)
            # User said "Height same as Start/Stop btn, Width maintained". Start/Stop height depends on font/padding.
            # Start/Stop with padding will be roughly 11+4+2+2 ~ 19-20px? Or higher? 
            # Automation Start/Stop height isn't fixed, it's content based.
            # I'll make reset button height variable or fixed small, say 24px height, and width 24px.
            # But "Height same as Start/Stop". Start/Stop might be smaller than 24px.
            # Let's remove fixed height for both and let layout handle, or set fixed height.
            # Automation button CSS didn't set fixed height.
            # I will set Reset button to look similar.
            
            reset_btn = QPushButton()
            # reset_btn.setObjectName("secondaryBtn") # Remove to use custom style
            reset_btn.setFixedSize(24, 24)
            
            reset_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
            reset_btn.setIconSize(QSize(12, 12))
            reset_btn.setToolTip("통계 초기화")
            reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            # Match style with toggle_btn for alignment
            reset_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {COLORS['text_primary']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 3px;
                    padding: 0px;
                    margin: 0px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['bg_hover']};
                    border-color: {COLORS['text_primary']};
                }}
            """)
            
            reset_btn.clicked.connect(lambda _, idx=index: self._reset_log_counter(idx))
            action_layout.addWidget(reset_btn)

            bottom_row.addLayout(action_layout)
            
            # Align Action Layout vertically to bottom? Or Center?
            # "Status/Start/Stop/Reset same x-axis as Count/Start Time combined".
            # Since Left is 2 lines, Right is 1 line. Center vertical alignment is best.
            # QHBoxLayout aligns center by default if stretch not weird.
            
            item_layout.addLayout(bottom_row)

            counter_layout.addWidget(item_frame)
            self._log_counters.append({
                "input": text_input,
                "count_label": count_label,
                "started_label": started_at_label,
                "status_label": status_label,
                "toggle_btn": toggle_btn,
                "count": 0,
                "started_at": None,
                "is_running": False,
                "is_stopped": False,
            })
            self._update_log_counter_ui(index)

        counter_layout.addStretch()
        counter_scroll.setWidget(counter_container)
        counter_scroll.setMinimumHeight(190)
        find_layout.addWidget(counter_scroll)
        layout.addWidget(find_group)

        # === 자동 명령 정보 및 목록 섹션 (New) ===
        auto_info_group = QGroupBox("자동 명령 정보")
        auto_info_layout = QVBoxLayout(auto_info_group)
        auto_info_layout.setContentsMargins(10, 8, 10, 10)
        auto_info_layout.setSpacing(4)

        # 대소문자 구분 (New)
        self._auto_case_checkbox = QCheckBox("대소문자 구분")
        self._auto_case_checkbox.setChecked(False)
        auto_info_layout.addWidget(self._auto_case_checkbox)

        # 스크롤 영역
        self._auto_list_scroll = QScrollArea()
        self._auto_list_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._auto_list_scroll.setWidgetResizable(True)
        self._auto_list_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # self._auto_list_scroll.setMaximumHeight(200)

        self._auto_list_container = QWidget()
        self._auto_list_layout = QVBoxLayout(self._auto_list_container)
        self._auto_list_layout.setContentsMargins(0, 0, 0, 0)
        self._auto_list_layout.setSpacing(4)
        self._auto_list_layout.addStretch()

        self._auto_list_scroll.setWidget(self._auto_list_container)
        auto_info_layout.addWidget(self._auto_list_scroll)
        
        layout.addWidget(auto_info_group)
        
        # Ratio & Size Policy
        find_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        auto_info_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        layout.setStretchFactor(find_group, 6)
        layout.setStretchFactor(auto_info_group, 4)

        # 하단 여백
        layout.addStretch()

        # 초기 포트 스캔
        self.refresh_ports()

    # (Existing Methods: refresh_ports, _on_connect_clicked, ...)

    def _make_robot_icon(self, size: int=16) -> QIcon:
        """자동 명령 아이콘 생성 (봇 모양)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(0,0,0,0))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(QFont("Noto Sans Emoji", 12))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "🤖")
        painter.end()
        return QIcon(pixmap)

    # === 자동 명령 수행 관리 ===

    def _add_automation_task(self):
        """새 자동 명령 추가 (최대 MAX_AUTO_TASKS)"""
        if len(self._automation_tasks) >= self.MAX_AUTO_TASKS:
            QMessageBox.warning(self, "추가 실패", f"자동 명령은 최대 {self.MAX_AUTO_TASKS}개까지만 등록할 수 있습니다.")
            return
        
        # 빈 태스크로 다이얼로그 열기
        dialog = AutomationDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self._automation_tasks.append(data)
            self._refresh_automation_list()
            
            # 사전 명령 즉시 실행 여부: 
            # requirement doesn't specify when "start" happens. 
            # "Name click to edit". "Status display".
            # Assuming tasks are "active" immediately if enabled?
            # Or should there be a global "Start Automation" toggle?
            # Requirement 9: "Execute... interval".
            # Let's assume enabling a task makes it active immediately.
            # And execute pre-cmd immediately if enabled?
            if data['enabled'] and data['pre_cmd'].strip():
                # "사전 명령 (시작 시 수행)" - probably when task is created or enabled?
                # For safety, maybe execute when added/enabled.
                self.send_command_requested.emit(data['pre_cmd'], data['cmd_interval'])

    def _edit_automation_task(self, index: int):
        """기존 자동 명령 수정"""
        if index < 0 or index >= len(self._automation_tasks):
            return
            
        task = self._automation_tasks[index]
        dialog = AutomationDialog(self, task)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_data()
            self._automation_tasks[index] = new_data
            self._refresh_automation_list()
            
            # If re-enabled or just edited, do we re-run pre-cmd?
            # Maybe ask user or just run if enabled?
            # Let's run pre-cmd if enabled, assuming it's an initialization.
            if new_data['enabled'] and new_data['pre_cmd'].strip():
                self.send_command_requested.emit(new_data['pre_cmd'], new_data['cmd_interval'])

    def _refresh_automation_list(self):
        """자동 명령 목록 UI 갱신"""
        # 기존 아이템 제거
        while self._auto_list_layout.count():
            item = self._auto_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 목록 재생성
        for i, task in enumerate(self._automation_tasks):
            item_frame = QFrame()
            item_frame.setStyleSheet(
                f"background-color: {COLORS['bg_input']}; border-radius: 4px;"
            )
            frame_layout = QHBoxLayout(item_frame)
            frame_layout.setContentsMargins(8, 6, 8, 6)
            frame_layout.setSpacing(8)
            
            # Name (Clickable)
            name_text = task['name']
            is_enabled = task['enabled']
            
            if is_enabled:
                name_style = f"color: {COLORS['accent']}; font-weight: bold;"
            else:
                name_style = f"color: {COLORS['text_disabled']}; font-weight: normal;"

            # Name & Count Layout
            name_layout = QHBoxLayout()
            name_layout.setContentsMargins(0, 0, 0, 0)
            name_layout.setSpacing(4)
            
            name_btn = QPushButton(name_text)
            name_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    {name_style}
                    text-align: left;
                    border: none;
                }}
                QPushButton:hover {{
                    text-decoration: underline;
                }}
            """)
            name_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            name_btn.clicked.connect(lambda _, idx=i: self._edit_automation_task(idx))
            name_layout.addWidget(name_btn)
            
            count = task.get('trigger_count', 0)
            if count > 0:
                count_lbl = QLabel(f"({count})")
                count_lbl.setStyleSheet(f"color: {COLORS['success']}; font-weight: bold; font-size: 11px;")
                name_layout.addWidget(count_lbl)
                
            name_layout.addStretch()
            frame_layout.addLayout(name_layout, 1) # stretch
            
            # Status text
            if is_enabled:
                status_text = "ON"
                status_color = COLORS['success']
            else:
                status_text = "OFF"
                status_color = COLORS['error']

            status_lbl = QLabel(status_text)
            status_lbl.setStyleSheet(f"color: {status_color}; font-weight: bold; font-size: 11px;")
            status_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            frame_layout.addWidget(status_lbl)

            # Start/Stop Control
            if is_enabled:
                 ctl_text = "Stop"
                 ctl_color = COLORS['error']
                 ctl_callback = lambda _, idx=i: self._stop_task(idx)
            else:
                 ctl_text = "Start"
                 ctl_color = COLORS['success']
                 ctl_callback = lambda _, idx=i: self._start_task(idx)

            ctl_btn = QPushButton(ctl_text)
            ctl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            ctl_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {ctl_color};
                    border: 1px solid {ctl_color};
                    border-radius: 3px;
                    padding: 2px 8px;
                    font-size: 11px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {ctl_color};
                    color: #FFFFFF;
                }}
            """)
            ctl_btn.clicked.connect(ctl_callback)
            frame_layout.addWidget(ctl_btn)

            # Delete Button
            del_btn = QPushButton("Del")
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {COLORS['text_secondary']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 3px;
                    padding: 2px 8px;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['error']};
                    color: #FFFFFF;
                    border-color: {COLORS['error']};
                }}
            """)
            del_btn.clicked.connect(lambda _, idx=i: self._delete_automation_task(idx))
            frame_layout.addWidget(del_btn)

            self._auto_list_layout.addWidget(item_frame)
            
        self._auto_list_layout.addStretch()

    def _delete_automation_task(self, index: int):
        """자동 명령 삭제"""
        if 0 <= index < len(self._automation_tasks):
            self._automation_tasks.pop(index)
            self._refresh_automation_list()

    def _start_task(self, index: int):
        """자동 명령 시작"""
        if 0 <= index < len(self._automation_tasks):
            task = self._automation_tasks[index]
            if not task['enabled']:
                task['enabled'] = True
                self._refresh_automation_list()
                
                # 시작 시 사전 명령 수행
                pre_cmd = task.get('pre_cmd', '').strip()
                if pre_cmd:
                    self.send_command_requested.emit(pre_cmd, task.get('cmd_interval', 0))

    def _stop_task(self, index: int):
        """자동 명령 정지"""
        if 0 <= index < len(self._automation_tasks):
            task = self._automation_tasks[index]
            if task['enabled']:
                task['enabled'] = False
                self._refresh_automation_list()

    def process_log_line_for_automation(self, line: str):
        """로그 라인 트리거 검사 및 사후 명령 예약"""
        triggered_any = False
        
        # 대소문자 구분 설정
        case_sensitive = self._auto_case_checkbox.isChecked()
        check_line = line if case_sensitive else line.lower()

        for task in self._automation_tasks:
            if not task['enabled']:
                continue
            
            trigger = task['trigger']
            if not trigger:
                continue

            check_trigger = trigger if case_sensitive else trigger.lower()

            if check_trigger in check_line:
                # Triggered!
                task['trigger_count'] = task.get('trigger_count', 0) + 1
                triggered_any = True
                
                delay_ms = task.get('delay', 0)
                cmd_interval = task.get('cmd_interval', 0)
                post_cmd = task.get('post_cmd', '')
                
                if delay_ms > 0:
                    QTimer.singleShot(
                        delay_ms, 
                        lambda c=post_cmd, i=cmd_interval: self.send_command_requested.emit(c, i)
                    )
                else:
                    if post_cmd:
                        self.send_command_requested.emit(post_cmd, cmd_interval)
                        
        if triggered_any:
            self._refresh_automation_list()

    # ... Existing helper methods (_make_copy_icon, _update_log_counter_label etc) ...

    def refresh_ports(self):
        """시리얼 포트 목록 새로고침"""
        self._port_combo.clear()
        ports = SerialManager.scan_ports()
        if ports:
            for port_info in ports:
                self._port_combo.addItem(
                    f"{port_info['path']}  ({port_info['description']})",
                    port_info["path"]
                )
        else:
            self._port_combo.addItem("포트를 찾을 수 없음")

    def _on_connect_clicked(self):
        """연결/해제 버튼 클릭"""
        if self._is_connected:
            self.disconnect_requested.emit()
        else:
            port = self._port_combo.currentData()
            if not port:
                return
            max_lines = int(self._max_lines_input.text() or 1_000_000)
            settings = {
                "port": port,
                "baudrate": self._baud_combo.currentData(),
                "databits": self._data_combo.currentData(),
                "parity": self._parity_combo.currentData(),
                "stopbits": self._stop_combo.currentData(),
                "max_lines": max_lines,
            }
            self.connect_requested.emit(settings)

    def set_actual_log_filename(self, filepath: str):
        """실제 생성된 로그 파일 경로 표시"""
        if filepath:
            # 절대 경로 표시
            abs_path = os.path.abspath(filepath)
            self._log_actual_label.setText(abs_path)
            self._log_actual_label.setToolTip(abs_path)
            self._log_actual_label.setStyleSheet(
                f"background-color: transparent; color: {COLORS['text_primary']}; font-size: 11px;"
            )
            self._log_copy_btn.setEnabled(True)
        else:
            self._log_actual_label.setText("-")
            self._log_actual_label.setToolTip("")
            self._log_actual_label.setStyleSheet(
                f"background-color: transparent; color: {COLORS['text_secondary']}; font-size: 11px;"
            )
            self._log_copy_btn.setEnabled(False)

    def set_stats_output_from_logfile(self, logfile_path: str):
        """로그 파일 경로로 통계 CSV 경로 생성/표시"""
        if not logfile_path:
            self._stats_csv_path = ""
            self._stats_file_label.setText("-")
            self._stats_file_label.setToolTip("")
            self._stats_file_label.setStyleSheet(
                f"background-color: transparent; color: {COLORS['text_secondary']}; font-size: 11px;"
            )
            self._stats_copy_btn.setEnabled(False)
            return

        self._stats_csv_path = self._build_stats_csv_path(logfile_path)
        self._stats_file_label.setText(self._stats_csv_path)
        self._stats_file_label.setToolTip(self._stats_csv_path)
        self._stats_file_label.setStyleSheet(
            f"background-color: transparent; color: {COLORS['text_primary']}; font-size: 11px;"
        )
        self._stats_copy_btn.setEnabled(True)

    @staticmethod
    def _build_stats_csv_path(logfile_path: str) -> str:
        """로그 파일명 타임스탬프를 활용해 통계 CSV 경로 생성"""
        abs_dir = os.path.dirname(os.path.abspath(logfile_path))
        log_filename = os.path.basename(logfile_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if log_filename.startswith("lnxterm_"):
            stem, _ = os.path.splitext(log_filename)
            extracted = stem[len("lnxterm_"):]
            if extracted:
                timestamp = extracted

        return os.path.join(abs_dir, f"lnxterm_stats_{timestamp}.csv")

    def set_log_started_time(self, timestamp: str):
        """로깅 시작 시간 표시"""
        if timestamp:
            self._log_started_label.setText(f"로깅 시작 시간: {timestamp}")
            self._log_started_label.setStyleSheet(
                f"background-color: transparent; color: {COLORS['warning']}; font-size: 11px;"
            )
        else:
            self._log_started_label.setText("로깅 시작 시간: -")
            self._log_started_label.setStyleSheet(
                f"background-color: transparent; color: {COLORS['text_secondary']}; font-size: 11px;"
            )

    def set_connected_state(self, connected: bool):
        """연결 상태 UI 업데이트"""
        self._is_connected = connected
        if connected:
            self._connect_btn.setObjectName("disconnectBtn")
            self._connect_btn.setIcon(
                self._make_power_icon(is_on=False)
            )
            self._connect_btn.setToolTip("연결 해제")
            self._port_combo.setEnabled(False)
            self._baud_combo.setEnabled(False)
            self._data_combo.setEnabled(False)
            self._parity_combo.setEnabled(False)
            self._stop_combo.setEnabled(False)
            self._max_lines_input.setEnabled(False)
            self._refresh_btn.setEnabled(False)
        else:
            self._connect_btn.setObjectName("")
            self._connect_btn.setIcon(
                self._make_power_icon(is_on=True)
            )
            self._connect_btn.setToolTip("연결")
            self._port_combo.setEnabled(True)
            self._baud_combo.setEnabled(True)
            self._data_combo.setEnabled(True)
            self._parity_combo.setEnabled(True)
            self._stop_combo.setEnabled(True)
            self._max_lines_input.setEnabled(True)
            self._refresh_btn.setEnabled(True)

        # 스타일 재적용 (objectName 변경 반영)
        self._connect_btn.style().unpolish(self._connect_btn)
        self._connect_btn.style().polish(self._connect_btn)

    def _on_conn_toggle(self, checked: bool):
        """연결 설정 토글 핸들러"""
        self._conn_content_widget.setVisible(checked)
        self._conn_toggle_btn.setText("연결 설정 ▼" if checked else "연결 설정 ▲")

    @staticmethod
    def _make_broom_icon(size: int = 22) -> QIcon:
        """터미널 클리어 버튼용 빗자루 아이콘 생성 (크기 확대)."""
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(0, 0, 0, 0))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        font = QFont("Noto Sans Emoji")
        font.setPointSize(int(size * 0.75)) # Scale font with size
        painter.setFont(font)
        painter.setPen(QColor(COLORS["text_primary"]))
        painter.drawText(
            pixmap.rect(),
            Qt.AlignmentFlag.AlignCenter,
            "🧹"
        )
        painter.end()

        return QIcon(pixmap)

    @staticmethod
    def _make_power_icon(is_on: bool, size: int = 16) -> QIcon:
        """연결/해제 버튼용 전원 아이콘 생성."""
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(0, 0, 0, 0))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        font = QFont("Noto Sans Emoji", int(size * 0.7))
        painter.setFont(font)

        if is_on:
            # Connect Button State (Ready to Connect) -> White Icon on Blue Background
            # Use Power Symbol
            painter.setPen(QColor("white"))
            painter.drawText(
                pixmap.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "⏻"
            )
        else:
            # Disconnect Button State (Connected) -> Cutting Cord Icon
            # Use Plug + Scissors or specialized unicode if available?
            # Or "✂️" over "🔌"?
            # Draw Plug
            painter.setPen(QColor(COLORS["text_primary"]))
            rect = pixmap.rect()
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "🔌")
            
            # Draw Red X or Cut
            painter.setPen(QColor(COLORS["error"]))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            # Draw a diagonal line or X
            # painter.drawLine(rect.topLeft(), rect.bottomRight())
            # painter.drawLine(rect.bottomLeft(), rect.topRight())
            # Or draw a 'scissors' emoji small?
            # Let's just draw a red slash over it
            width = rect.width()
            height = rect.height()
            painter.drawLine(int(width*0.2), int(height*0.2), int(width*0.8), int(height*0.8))
            painter.drawLine(int(width*0.8), int(height*0.2), int(width*0.2), int(height*0.8))

        painter.end()

        return QIcon(pixmap)

    def set_logging_state(self, logging: bool, clear_display: bool = True):
        """로깅 상태 UI 업데이트"""
        self._is_logging = logging
        if not logging and clear_display:
            self.set_log_started_time("")
            self.set_actual_log_filename("")

    def _update_log_counter_ui(self, index: int):
        """카운터 UI 상태 갱신 (라벨, 버튼, 상태 등)"""
        counter = self._log_counters[index]
        is_running = counter["is_running"]
        is_stopped = counter["is_stopped"]
        
        # Colors
        active_color = COLORS["success"]
        inactive_color = COLORS["text_disabled"] # or text_secondary
        
        if is_running:
            label_color = active_color
        else:
            label_color = inactive_color

        # 1. Labels
        counter["count_label"].setText(f"Count: {counter['count']}")
        counter["count_label"].setStyleSheet(
            f"color: {label_color}; font-size: 11px; font-weight: bold; background-color: transparent; border: none;"
        )
        
        if counter["started_at"] is None or counter["started_at"] == 0:
            started_text = "Start: -"
        else:
            full_started_at = counter["started_at"].strftime("%Y-%m-%d %H:%M:%S")
            started_text = f"Start: {full_started_at}"
            
        counter["started_label"].setText(started_text)
        counter["started_label"].setStyleSheet(
            f"color: {label_color}; font-size: 11px; background-color: transparent; border: none;"
        )

        # 2. Status & Loop Control
        if is_running:
            status_text = "ON"
            status_color = COLORS["success"]
            ctl_text = "Stop"
            ctl_color = COLORS["error"]
        else:
            status_text = "OFF"
            status_color = COLORS["error"] # Red/Grey for OFF
            ctl_text = "Start"
            ctl_color = COLORS["success"]
            
        counter["status_label"].setText(status_text)
        counter["status_label"].setStyleSheet(f"color: {status_color}; font-weight: bold; font-size: 11px; border: none;")
        
        # 3. Toggle Button
        btn = counter["toggle_btn"]
        btn.setText(ctl_text)
        # Style matches Automation Info toggle button (padding 2px 8px)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {ctl_color};
                border: 1px solid {ctl_color};
                border-radius: 3px;
                padding: 0px;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {ctl_color};
                color: #FFFFFF;
            }}
        """)
        
        # Text Input Color match status if running
        if is_running:
             counter["input"].setStyleSheet(f"color: {COLORS['success']}; font-weight: bold;")
        else:
             counter["input"].setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: normal;")

    @staticmethod
    def _make_copy_icon(size: int = 8) -> QIcon:
        """복사 아이콘 생성."""
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(0, 0, 0, 0))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QColor(COLORS["accent"]))
        painter.setBrush(QColor(0, 0, 0, 0))
        painter.drawRect(1, 1, size - 3, size - 4)
        painter.drawRect(3, 3, size - 5, size - 4)
        painter.setPen(QColor(COLORS["terminal_white"]))
        painter.drawLine(size - 4, 2, size - 2, 2)
        painter.drawLine(size - 4, 4, size - 2, 4)
        painter.end()

        return QIcon(pixmap)

    def _copy_log_path(self):
        """현재 로그 파일 경로를 클립보드로 복사"""
        text = self._log_actual_label.text().strip()
        if text and text != "-":
            QApplication.clipboard().setText(text)

    def _copy_stats_path(self):
        """현재 통계 파일 경로를 클립보드로 복사"""
        text = self._stats_file_label.text().strip()
        if text and text != "-":
            QApplication.clipboard().setText(text)

    def _set_counter_readonly(self, index: int, readonly: bool):
        """카운터 입력칸 편집 가능 상태 제어"""
        counter = self._log_counters[index]
        counter["input"].setReadOnly(readonly)

    def _toggle_log_counter(self, index: int):
        """카운터 시작/정지 토글"""
        counter = self._log_counters[index]
        if counter["is_running"]:
            self._stop_log_counter(index)
        else:
            self._start_log_counter(index)

    def _start_log_counter(self, index: int):
        """특정 카운터 집계 시작"""
        counter = self._log_counters[index]
        keyword = counter["input"].text().strip()
        if not keyword:
            return

        if counter["started_at"] is None or counter["started_at"] == 0:
            counter["started_at"] = datetime.now()
        counter["is_running"] = True
        counter["is_stopped"] = False
        self._set_counter_readonly(index, True)
        self._update_log_counter_ui(index)

    def _on_log_keyword_changed(self, index: int):
        """입력값 변경 시 해당 통계 초기 상태로 전환"""
        counter = self._log_counters[index]
        counter["count"] = 0
        counter["started_at"] = None
        counter["is_running"] = False
        counter["is_stopped"] = False
        self._update_log_counter_ui(index)

    def _reset_log_counter(self, index: int):
        """특정 카운터 초기화"""
        counter = self._log_counters[index]
        counter["count"] = 0
        counter["started_at"] = 0
        counter["is_running"] = False
        counter["is_stopped"] = False
        counter["input"].setText("")
        self._set_counter_readonly(index, False)
        self._update_log_counter_ui(index)

    def _reset_all_log_counters(self):
        """문자열 통계 모든 항목 초기화"""
        for index in range(len(self._log_counters)):
            self._reset_log_counter(index)

    def _stop_log_counter(self, index: int):
        """특정 카운터 집계 정지 및 정지 표시"""
        counter = self._log_counters[index]
        counter["is_running"] = False
        counter["is_stopped"] = True
        self._set_counter_readonly(index, True)
        self._update_log_counter_ui(index)

    def _append_counter_stats(self, keyword: str, count: int, timestamp: str | None, log_line: str):
        """통계 변경 내역을 CSV 파일에 저장"""
        if not self._stats_csv_path:
            return

        os.makedirs(os.path.dirname(self._stats_csv_path), exist_ok=True)
        normalized_time = self._normalize_stats_timestamp(timestamp)
        needs_header = (
            not os.path.exists(self._stats_csv_path)
            or os.path.getsize(self._stats_csv_path) == 0
        )

        try:
            with open(self._stats_csv_path, "a", newline="", encoding="utf-8") as fp:
                writer = csv.writer(fp)
                if needs_header:
                    writer.writerow(["문자열", "집계 시점", "누적 카운트", "대소문자 구분", "로그"])
                writer.writerow(
                    [
                        keyword,
                        normalized_time,
                        count,
                        "예" if self._case_sensitive_checkbox.isChecked() else "아니오",
                        log_line,
                    ]
                )
        except OSError:
            # 통계 저장은 보조 기능이므로 기록 실패가 메인 동작을 멈추지 않게 함
            return

    @staticmethod
    def _normalize_stats_timestamp(timestamp: str | None) -> str:
        """타임스탬프 문자열 정규화"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        if not timestamp:
            return now

        timestamp = timestamp.strip()
        if timestamp.startswith("[") and "]" in timestamp:
            return timestamp[1:timestamp.rfind("]")]
        return timestamp

    def process_log_line_for_counters(self, line: str, line_timestamp: str = None):
        """로그 라인 출력 시 문자열 카운터 누적"""
        if self._case_sensitive_checkbox.isChecked():
            compare_line = line
        else:
            compare_line = line.lower()
        for index, counter in enumerate(self._log_counters):
            keyword = counter["input"].text().strip()
            if not keyword:
                continue
            if not counter["is_running"]:
                continue
            compare_keyword = keyword if self._case_sensitive_checkbox.isChecked() else keyword.lower()
            if compare_keyword in compare_line:
                counter["count"] += 1
                self._append_counter_stats(
                    keyword,
                    counter["count"],
                    line_timestamp,
                    line.rstrip("\r\n")
                )
                self._update_log_counter_ui(index)

    # === 자동 명령 수행 ===


