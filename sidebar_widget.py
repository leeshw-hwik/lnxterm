"""
사이드바 위젯: 포트 설정, 연결 제어, 로그 파일
"""

import serial.tools.list_ports
import os
from datetime import datetime
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QGroupBox, QGridLayout, QLineEdit, QScrollArea, QStyle,
    QWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize

from serial_manager import SerialManager
from styles import COLORS


class SidebarWidget(QFrame):
    """사이드바 패널 위젯"""

    MAX_LOG_COUNTERS = 10

    # 시그널
    connect_requested = pyqtSignal(dict)    # 연결 요청 (설정 딕셔너리)
    disconnect_requested = pyqtSignal()     # 연결 해제 요청
    log_stop_requested = pyqtSignal()       # 로그 중지
    clear_requested = pyqtSignal()          # 터미널 클리어

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setMinimumWidth(240)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        self._is_connected = False
        self._is_logging = False
        self._log_counters = []

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
        self._connect_btn.setFixedSize(30, 30)
        self._connect_btn.setIconSize(QSize(16, 16))
        self._connect_btn.setToolTip("연결")
        self._connect_btn.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
        )
        self._connect_btn.clicked.connect(self._on_connect_clicked)
        action_layout.addWidget(self._connect_btn)

        self._clear_btn = QPushButton()
        self._clear_btn.setObjectName("secondaryBtn")
        self._clear_btn.setFixedSize(30, 30)
        self._clear_btn.setIconSize(QSize(16, 16))
        self._clear_btn.setToolTip("터미널 클리어")
        self._clear_btn.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon)
        )
        self._clear_btn.clicked.connect(self.clear_requested.emit)
        action_layout.addWidget(self._clear_btn)
        action_layout.addStretch()

        layout.addWidget(action_row)

        # === 연결 설정 섹션 ===
        conn_group = QGroupBox("연결 설정")
        conn_layout = QGridLayout(conn_group)
        conn_layout.setHorizontalSpacing(8)
        conn_layout.setVerticalSpacing(8)
        conn_layout.setContentsMargins(10, 14, 10, 10)
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

        port_widget = QWidget()
        port_widget.setLayout(port_row)
        add_conn_row(0, "포트:", port_widget)

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

        layout.addWidget(conn_group)

        # === 로그 정보 섹션 ===
        log_group = QGroupBox("로그 파일")
        log_group.setObjectName("logGroup")
        log_layout = QVBoxLayout(log_group)
        log_layout.setSpacing(8)
        log_layout.setContentsMargins(10, 4, 10, 10)

        # 로깅 시작 시간 표시
        self._log_started_label = QLabel("시작 시간: -")
        self._log_started_label.setStyleSheet(
            "background-color: transparent; color: #808080; font-size: 11px;"
        )
        self._log_started_label.setWordWrap(True)
        log_layout.addWidget(self._log_started_label)

        # 현재 로그 파일 표시
        self._log_actual_label = QLabel("로그 대기 중...")
        self._log_actual_label.setStyleSheet(
            "background-color: transparent; color: #808080; font-size: 11px;"
        )
        self._log_actual_label.setWordWrap(True)
        self._log_actual_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        log_layout.addWidget(self._log_actual_label)

        layout.addWidget(log_group)

        # === 문자열 찾기 섹션 ===
        find_group = QGroupBox("문자열 찾기")
        find_layout = QVBoxLayout(find_group)
        find_layout.setSpacing(8)
        find_layout.setContentsMargins(10, 20, 10, 10)

        # 문자열 찾기 입력 목록 (최대 10개)
        counter_scroll = QScrollArea()
        counter_scroll.setFrameShape(QFrame.Shape.NoFrame)
        counter_scroll.setWidgetResizable(True)
        counter_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        counter_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        counter_container = QWidget()
        counter_layout = QVBoxLayout(counter_container)
        counter_layout.setContentsMargins(0, 0, 0, 0)
        counter_layout.setSpacing(6)

        for index in range(self.MAX_LOG_COUNTERS):
            item_frame = QFrame()
            item_frame.setStyleSheet(
                "QFrame { border: 1px solid #3c3c3c; border-radius: 4px; background-color: transparent; }"
            )
            item_layout = QVBoxLayout(item_frame)
            item_layout.setContentsMargins(6, 6, 6, 6)
            item_layout.setSpacing(3)

            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(4)

            text_input = QLineEdit()
            text_input.setPlaceholderText(f"문자열 {index + 1}")
            text_input.setMinimumHeight(28)
            text_input.textChanged.connect(
                lambda _text, idx=index: self._reset_log_counter(idx)
            )
            row_layout.addWidget(text_input, 1)
            item_layout.addLayout(row_layout)

            bottom_row = QHBoxLayout()
            bottom_row.setContentsMargins(0, 0, 0, 0)
            bottom_row.setSpacing(4)

            info_layout = QVBoxLayout()
            info_layout.setContentsMargins(0, 0, 0, 0)
            info_layout.setSpacing(2)

            count_label = QLabel("카운트: 0")
            count_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            count_label.setStyleSheet(
                "background-color: transparent; color: #4ec9b0; font-size: 10px; border: none;"
            )
            info_layout.addWidget(count_label)

            started_at_label = QLabel("시작 시간: -")
            started_at_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            started_at_label.setStyleSheet(
                "background-color: transparent; color: #808080; font-size: 10px; border: none;"
            )
            info_layout.addWidget(started_at_label)

            bottom_row.addLayout(info_layout, 1)

            reset_btn = QPushButton()
            reset_btn.setObjectName("secondaryBtn")
            reset_btn.setFixedSize(24, 24)
            reset_btn.setIconSize(QSize(14, 14))
            reset_btn.setToolTip("카운트 초기화")
            reset_btn.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload)
            )
            reset_btn.clicked.connect(
                lambda _checked=False, idx=index: self._reset_log_counter(idx)
            )
            bottom_row.addWidget(
                reset_btn,
                0,
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )

            item_layout.addLayout(bottom_row)

            counter_layout.addWidget(item_frame)
            self._log_counters.append({
                "input": text_input,
                "count_label": count_label,
                "started_label": started_at_label,
                "count": 0,
                "started_at": None,
            })

        counter_layout.addStretch()
        counter_scroll.setWidget(counter_container)
        counter_scroll.setMinimumHeight(190)
        find_layout.addWidget(counter_scroll)
        layout.addWidget(find_group)

        # 하단 여백
        layout.addStretch()

        # 초기 포트 스캔
        self.refresh_ports()

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
            settings = {
                "port": port,
                "baudrate": self._baud_combo.currentData(),
                "databits": self._data_combo.currentData(),
                "parity": self._parity_combo.currentData(),
                "stopbits": self._stop_combo.currentData(),
            }
            self.connect_requested.emit(settings)

    def set_actual_log_filename(self, filepath: str):
        """실제 생성된 로그 파일 경로 표시"""
        if filepath:
            # 절대 경로 표시
            abs_path = os.path.abspath(filepath)
            self._log_actual_label.setText(f"▶ {abs_path}")
            self._log_actual_label.setToolTip(abs_path)
            self._log_actual_label.setStyleSheet(
                "background-color: transparent; color: #4ec9b0; font-size: 11px;"
            )
        else:
            self._log_actual_label.setText("로그 대기 중...")
            self._log_actual_label.setToolTip("")
            self._log_actual_label.setStyleSheet(
                "background-color: transparent; color: #808080; font-size: 11px;"
            )

    def set_log_started_time(self, timestamp: str):
        """로깅 시작 시간 표시"""
        if timestamp:
            self._log_started_label.setText(f"시작 시간: {timestamp}")
            self._log_started_label.setStyleSheet(
                "background-color: transparent; color: #d7ba7d; font-size: 11px;"
            )
        else:
            self._log_started_label.setText("시작 시간: -")
            self._log_started_label.setStyleSheet(
                "background-color: transparent; color: #808080; font-size: 11px;"
            )

    def set_connected_state(self, connected: bool):
        """연결 상태 UI 업데이트"""
        self._is_connected = connected
        if connected:
            self._connect_btn.setObjectName("disconnectBtn")
            self._connect_btn.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop)
            )
            self._connect_btn.setToolTip("연결 해제")
            self._port_combo.setEnabled(False)
            self._baud_combo.setEnabled(False)
            self._data_combo.setEnabled(False)
            self._parity_combo.setEnabled(False)
            self._stop_combo.setEnabled(False)
            self._refresh_btn.setEnabled(False)
        else:
            self._connect_btn.setObjectName("")
            self._connect_btn.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
            )
            self._connect_btn.setToolTip("연결")
            self._port_combo.setEnabled(True)
            self._baud_combo.setEnabled(True)
            self._data_combo.setEnabled(True)
            self._parity_combo.setEnabled(True)
            self._stop_combo.setEnabled(True)
            self._refresh_btn.setEnabled(True)

        # 스타일 재적용 (objectName 변경 반영)
        self._connect_btn.style().unpolish(self._connect_btn)
        self._connect_btn.style().polish(self._connect_btn)

    def set_logging_state(self, logging: bool):
        """로깅 상태 UI 업데이트"""
        self._is_logging = logging
        if not logging:
            self.set_log_started_time("")
            self.set_actual_log_filename("")

    def _update_log_counter_label(self, index: int):
        """카운터 라벨 텍스트 갱신"""
        counter = self._log_counters[index]
        counter["count_label"].setText(f"카운트: {counter['count']}")
        if counter["started_at"]:
            full_started_at = counter["started_at"].strftime("%Y-%m-%d %H:%M:%S")
            counter["started_label"].setText(f"시작 시간: {full_started_at}")
            counter["started_label"].setStyleSheet(
                "background-color: transparent; color: #d7ba7d; font-size: 10px; border: none;"
            )
        else:
            counter["started_label"].setText("시작 시간: -")
            counter["started_label"].setStyleSheet(
                "background-color: transparent; color: #808080; font-size: 10px; border: none;"
            )

    def _reset_log_counter(self, index: int):
        """특정 카운터 초기화"""
        counter = self._log_counters[index]
        counter["count"] = 0
        counter["started_at"] = None
        self._update_log_counter_label(index)

    def process_log_line_for_counters(self, line: str):
        """로그 라인 출력 시 문자열 카운터 누적"""
        for index, counter in enumerate(self._log_counters):
            keyword = counter["input"].text().strip()
            if not keyword:
                continue
            if keyword in line:
                counter["count"] += 1
                if counter["started_at"] is None:
                    counter["started_at"] = datetime.now()
                self._update_log_counter_label(index)
