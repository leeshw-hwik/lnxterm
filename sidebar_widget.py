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
    QApplication,
    QCheckBox,
    QWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIntValidator, QPainter, QPixmap, QIcon, QColor, QFont

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
        self._stats_csv_path = ""

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
        self._connect_btn.setIconSize(QSize(16, 16))
        self._connect_btn.setToolTip("연결")
        self._connect_btn.setIcon(
            self._make_power_icon(is_on=True)
        )
        self._connect_btn.clicked.connect(self._on_connect_clicked)
        action_layout.addWidget(self._connect_btn)

        self._clear_btn = QPushButton()
        self._clear_btn.setObjectName("secondaryBtn")
        self._clear_btn.setFixedSize(34, 34)
        self._clear_btn.setIconSize(QSize(16, 16))
        self._clear_btn.setToolTip("터미널 클리어")
        self._clear_btn.setIcon(self._make_broom_icon())
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
        add_conn_row(0, "Port:", port_widget)

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

        layout.addWidget(conn_group)

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
        self._reset_all_btn.setFixedHeight(24)
        self._reset_all_btn.setMinimumWidth(82)
        self._reset_all_btn.setToolTip("문자열 통계 전체 항목 초기화")
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
            item_layout.setContentsMargins(6, 6, 6, 6)
            item_layout.setSpacing(3)

            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(4)

            text_input = QLineEdit()
            text_input.setPlaceholderText(f"문자열 {index + 1}")
            text_input.setMinimumHeight(28)
            text_input.textChanged.connect(
                lambda _text, idx=index: self._on_log_keyword_changed(idx)
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
                f"background-color: transparent; color: {COLORS['success']}; font-size: 11px; border: none;"
            )
            info_layout.addWidget(count_label)

            started_at_label = QLabel("로깅 시작 시간: -")
            started_at_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            started_at_label.setStyleSheet(
                f"background-color: transparent; color: {COLORS['text_secondary']}; font-size: 11px; border: none;"
            )
            info_layout.addWidget(started_at_label)

            bottom_row.addLayout(info_layout, 1)

            start_btn = QPushButton()
            start_btn.setObjectName("secondaryBtn")
            start_btn.setFixedSize(24, 24)
            start_btn.setIconSize(QSize(14, 14))
            start_btn.setToolTip("통계 시작")
            start_btn.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
            )
            start_btn.clicked.connect(
                lambda _checked=False, idx=index: self._start_log_counter(idx)
            )
            bottom_row.addWidget(
                start_btn,
                0,
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )

            stop_btn = QPushButton()
            stop_btn.setObjectName("secondaryBtn")
            stop_btn.setFixedSize(24, 24)
            stop_btn.setIconSize(QSize(14, 14))
            stop_btn.setToolTip("통계 정지")
            stop_btn.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop)
            )
            stop_btn.clicked.connect(
                lambda _checked=False, idx=index: self._stop_log_counter(idx)
            )
            bottom_row.addWidget(
                stop_btn,
                0,
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )

            reset_btn = QPushButton()
            reset_btn.setObjectName("secondaryBtn")
            reset_btn.setFixedSize(24, 24)
            reset_btn.setIconSize(QSize(14, 14))
            reset_btn.setToolTip("문자열/카운트/시작시간 초기화")
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
                "is_running": False,
                "is_stopped": False,
            })
            self._update_log_counter_label(index)

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

    @staticmethod
    def _make_broom_icon(size: int = 16) -> QIcon:
        """터미널 클리어 버튼용 빗자루 아이콘 생성."""
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(0, 0, 0, 0))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        font = QFont("Noto Sans Emoji")
        font.setPointSize(12)
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

        pen = QColor(COLORS["text_primary"])
        painter.setPen(pen)
        painter.setBrush(QColor(0, 0, 0, 0))
        painter.setFont(QFont("Noto Sans", 12))

        painter.setPen(QColor(COLORS["success"]) if is_on else QColor(COLORS["text_primary"]))
        painter.drawText(
            pixmap.rect(),
            Qt.AlignmentFlag.AlignCenter,
            "⏻" if is_on else "⏼"
        )
        painter.end()

        return QIcon(pixmap)

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
        if counter["started_at"] is None:
            started_text = "로깅 시작 시간: -"
        elif counter["started_at"] == 0:
            started_text = "로깅 시작 시간: 0"
        else:
            full_started_at = counter["started_at"].strftime("%Y-%m-%d %H:%M:%S")
            started_text = f"로깅 시작 시간: {full_started_at}"

        if counter["is_running"]:
            status_color = COLORS["success"]
        elif counter["is_stopped"]:
            status_color = COLORS["error"]
        else:
            status_color = COLORS["text_secondary"]

        counter["started_label"].setText(started_text)
        counter["started_label"].setStyleSheet(
            f"background-color: transparent; color: {status_color}; font-size: 11px; border: none;"
        )
        counter["count_label"].setStyleSheet(
            f"background-color: transparent; color: {status_color}; font-size: 11px; border: none;"
        )
        counter["input"].setStyleSheet(
            f"color: {status_color};"
        )

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
        self._update_log_counter_label(index)

    def _on_log_keyword_changed(self, index: int):
        """입력값 변경 시 해당 통계 초기 상태로 전환"""
        counter = self._log_counters[index]
        counter["count"] = 0
        counter["started_at"] = None
        counter["is_running"] = False
        counter["is_stopped"] = False
        self._update_log_counter_label(index)

    def _reset_log_counter(self, index: int):
        """특정 카운터 초기화"""
        counter = self._log_counters[index]
        counter["count"] = 0
        counter["started_at"] = 0
        counter["is_running"] = False
        counter["is_stopped"] = False
        counter["input"].setText("")
        self._set_counter_readonly(index, False)
        self._update_log_counter_label(index)

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
        self._update_log_counter_label(index)

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
                self._update_log_counter_label(index)
