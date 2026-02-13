"""
사이드바 위젯: 포트 설정, 연결 제어, 로그 파일
"""

import serial.tools.list_ports
import os
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QGroupBox, QFormLayout,
    QWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal

from serial_manager import SerialManager
from styles import COLORS


class SidebarWidget(QFrame):
    """사이드바 패널 위젯"""

    # 시그널
    connect_requested = pyqtSignal(dict)    # 연결 요청 (설정 딕셔너리)
    disconnect_requested = pyqtSignal()     # 연결 해제 요청
    log_stop_requested = pyqtSignal()       # 로그 중지
    clear_requested = pyqtSignal()          # 터미널 클리어

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(260)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        self._is_connected = False
        self._is_logging = False

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # === 연결 설정 섹션 ===
        conn_group = QGroupBox("연결 설정")
        conn_layout = QFormLayout(conn_group)
        conn_layout.setSpacing(8)
        conn_layout.setContentsMargins(10, 20, 10, 10)

        # 포트 선택
        port_row = QHBoxLayout()
        self._port_combo = QComboBox()
        self._port_combo.setMinimumWidth(120)
        port_row.addWidget(self._port_combo, 1)

        self._refresh_btn = QPushButton("⟳")
        self._refresh_btn.setObjectName("secondaryBtn")
        self._refresh_btn.setFixedSize(32, 32)
        self._refresh_btn.setToolTip("포트 새로고침")
        self._refresh_btn.clicked.connect(self.refresh_ports)
        port_row.addWidget(self._refresh_btn)

        port_widget = QWidget()
        port_widget.setLayout(port_row)
        conn_layout.addRow("포트:", port_widget)

        # Baudrate 선택
        self._baud_combo = QComboBox()
        for rate in SerialManager.BAUDRATES:
            self._baud_combo.addItem(str(rate), rate)
        # 기본값 115200
        idx = self._baud_combo.findData(SerialManager.DEFAULT_BAUDRATE)
        if idx >= 0:
            self._baud_combo.setCurrentIndex(idx)
        conn_layout.addRow("Baud:", self._baud_combo)

        # Data Bits
        self._data_combo = QComboBox()
        for label, value in SerialManager.DATABITS.items():
            self._data_combo.addItem(label, value)
        self._data_combo.setCurrentIndex(3)  # 8 bits
        conn_layout.addRow("Data:", self._data_combo)

        # Parity
        self._parity_combo = QComboBox()
        for label, value in SerialManager.PARITIES.items():
            self._parity_combo.addItem(label, value)
        conn_layout.addRow("Parity:", self._parity_combo)

        # Stop Bits
        self._stop_combo = QComboBox()
        for label, value in SerialManager.STOPBITS.items():
            self._stop_combo.addItem(label, value)
        conn_layout.addRow("Stop:", self._stop_combo)

        layout.addWidget(conn_group)

        # 연결/해제 버튼
        self._connect_btn = QPushButton("🔌  연결")
        self._connect_btn.setMinimumHeight(36)
        self._connect_btn.clicked.connect(self._on_connect_clicked)
        layout.addWidget(self._connect_btn)

        # === 로그 정보 섹션 ===
        log_group = QGroupBox("로그 파일")
        log_layout = QVBoxLayout(log_group)
        log_layout.setSpacing(8)
        log_layout.setContentsMargins(10, 20, 10, 10)

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

        # === 도구 섹션 ===
        tools_group = QGroupBox("도구")
        tools_layout = QVBoxLayout(tools_group)
        tools_layout.setSpacing(8)
        tools_layout.setContentsMargins(10, 20, 10, 10)

        self._clear_btn = QPushButton("🗑  터미널 클리어")
        self._clear_btn.setObjectName("secondaryBtn")
        self._clear_btn.setMinimumHeight(32)
        self._clear_btn.clicked.connect(self.clear_requested.emit)
        tools_layout.addWidget(self._clear_btn)

        layout.addWidget(tools_group)

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

    def set_connected_state(self, connected: bool):
        """연결 상태 UI 업데이트"""
        self._is_connected = connected
        if connected:
            self._connect_btn.setText("🔌  연결 해제")
            self._connect_btn.setObjectName("disconnectBtn")
            self._port_combo.setEnabled(False)
            self._baud_combo.setEnabled(False)
            self._data_combo.setEnabled(False)
            self._parity_combo.setEnabled(False)
            self._stop_combo.setEnabled(False)
            self._refresh_btn.setEnabled(False)
        else:
            self._connect_btn.setText("🔌  연결")
            self._connect_btn.setObjectName("")
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
            self.set_actual_log_filename("")
