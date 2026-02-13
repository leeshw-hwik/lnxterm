"""
메인 윈도우: VS Code 스타일 레이아웃, 모든 위젯 통합
"""

import sys
import os
from datetime import datetime
from dotenv import load_dotenv, set_key
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QLineEdit, QLabel, QStatusBar, QPushButton,
    QMenuBar, QMessageBox, QApplication, QFrame
)
from PyQt6.QtGui import QAction, QShortcut, QKeySequence, QFont
from PyQt6.QtCore import Qt, QTimer

from serial_manager import SerialManager
from log_manager import LogManager
from terminal_widget import TerminalWidget
from search_widget import SearchWidget
from sidebar_widget import SidebarWidget
from styles import (
    get_main_stylesheet, get_command_input_stylesheet,
    get_statusbar_connected_stylesheet, get_statusbar_disconnected_stylesheet
)


class CommandInput(QLineEdit):
    """명령 입력 위젯 (히스토리 기능 포함)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(get_command_input_stylesheet())
        self.setPlaceholderText("명령을 입력하세요... (Enter로 전송)")

        self._history: list[str] = []
        self._history_index: int = -1
        self._max_history: int = 100

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Up:
            self._navigate_history(-1)
        elif event.key() == Qt.Key.Key_Down:
            self._navigate_history(1)
        else:
            super().keyPressEvent(event)

    def add_to_history(self, command: str):
        """명령 히스토리에 추가"""
        if command and (not self._history or self._history[-1] != command):
            self._history.append(command)
            if len(self._history) > self._max_history:
                self._history.pop(0)
        self._history_index = len(self._history)

    def _navigate_history(self, direction: int):
        """히스토리 탐색 (direction: -1=이전, 1=다음)"""
        if not self._history:
            return

        new_index = self._history_index + direction
        if new_index < 0:
            new_index = 0
        elif new_index >= len(self._history):
            new_index = len(self._history)
            self.clear()
            self._history_index = new_index
            return

        self._history_index = new_index
        self.setText(self._history[new_index])


class MainWindow(QMainWindow):
    """메인 윈도우"""

    APP_TITLE = "LnxTerm - 시리얼 터미널"

    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.APP_TITLE)
        self.setMinimumSize(1000, 650)
        self.resize(1280, 768)

        # .env 파일 로드
        self._env_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), ".env"
        )
        load_dotenv(self._env_path)
        self._log_dir = os.environ.get("LOG_DIR", "")

        # 매니저 초기화
        self._serial = SerialManager()
        self._log = LogManager()
        self._rx_bytes = 0
        self._tx_bytes = 0

        # 자동 재연결 설정
        self._last_settings: dict = {}
        self._auto_reconnect = True
        self._manual_disconnect = False
        self._reconnect_timer = QTimer(self)
        self._reconnect_timer.setInterval(3000)  # 3초
        self._reconnect_timer.timeout.connect(self._try_reconnect)

        # 스타일 적용
        self.setStyleSheet(get_main_stylesheet())

        # UI 구성
        self._setup_menu_bar()
        self._setup_central_widget()
        self._setup_status_bar()
        self._setup_shortcuts()

        # 시그널 연결
        self._connect_signals()

        # 초기 상태
        self._update_statusbar_style(False)
        self._terminal.append_system_message("LnxTerm 시리얼 터미널이 시작되었습니다.")

        # LOG_DIR 확인
        if self._log_dir:
            self._terminal.append_system_message(f"로그 디렉토리: {self._log_dir}")
        else:
            self._terminal.append_system_message("로그 디렉토리가 설정되지 않았습니다. 연결 시 설정합니다.")

        self._terminal.append_system_message("사이드바에서 포트를 선택하고 연결하세요.\n")

    def _setup_menu_bar(self):
        """메뉴바 구성"""
        menubar = self.menuBar()

        # 파일 메뉴
        file_menu = menubar.addMenu("파일(&F)")

        log_start_action = QAction("로그 시작...", self)
        log_start_action.setShortcut("Ctrl+L")
        log_start_action.triggered.connect(self._on_log_start_menu)
        file_menu.addAction(log_start_action)

        log_stop_action = QAction("로그 중지", self)
        log_stop_action.triggered.connect(self._on_log_stop)
        file_menu.addAction(log_stop_action)

        file_menu.addSeparator()

        exit_action = QAction("종료(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 편집 메뉴
        edit_menu = menubar.addMenu("편집(&E)")

        find_action = QAction("검색(&F)", self)
        find_action.setShortcut("Ctrl+F")
        find_action.triggered.connect(self._toggle_search)
        edit_menu.addAction(find_action)

        edit_menu.addSeparator()

        clear_action = QAction("터미널 클리어", self)
        clear_action.setShortcut("Ctrl+Shift+C")
        clear_action.triggered.connect(self._clear_terminal)
        edit_menu.addAction(clear_action)

        # 보기 메뉴
        view_menu = menubar.addMenu("보기(&V)")

        sidebar_action = QAction("사이드바 토글", self)
        sidebar_action.setShortcut("Ctrl+B")
        sidebar_action.triggered.connect(self._toggle_sidebar)
        view_menu.addAction(sidebar_action)

        refresh_action = QAction("포트 새로고침", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(lambda: self._sidebar.refresh_ports())
        view_menu.addAction(refresh_action)

        # 도움말 메뉴
        help_menu = menubar.addMenu("도움말(&H)")

        about_action = QAction("LnxTerm 정보", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_central_widget(self):
        """중앙 위젯 구성"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 사이드바
        self._sidebar = SidebarWidget()
        main_layout.addWidget(self._sidebar)

        # 오른쪽 영역 (터미널 + 검색 + 입력)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # 검색 위젯
        self._terminal = TerminalWidget()
        self._search = SearchWidget(self._terminal)
        right_layout.addWidget(self._search)

        # 터미널
        right_layout.addWidget(self._terminal, 1)

        # 명령 입력 바
        input_frame = QFrame()
        input_frame.setStyleSheet(f"background-color: #252526; border-top: 1px solid #3c3c3c;")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(8, 4, 8, 4)
        input_layout.setSpacing(8)

        prompt_label = QLabel("❯")
        prompt_label.setStyleSheet("color: #007acc; font-size: 16px; font-weight: bold; background-color: transparent;")
        input_layout.addWidget(prompt_label)

        self._command_input = CommandInput()
        self._command_input.returnPressed.connect(self._send_command)
        input_layout.addWidget(self._command_input, 1)

        # 전송 버튼
        send_btn = QPushButton("전송")
        send_btn.setFixedHeight(30)
        send_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        send_btn.clicked.connect(self._send_command)
        input_layout.addWidget(send_btn)

        right_layout.addWidget(input_frame)

        main_layout.addWidget(right_panel, 1)

    def _setup_status_bar(self):
        """상태바 구성"""
        self._statusbar = self.statusBar()

        self._status_connection = QLabel("⚫ 연결 안됨")
        self._status_port = QLabel("")
        self._status_baud = QLabel("")
        self._status_rx = QLabel("RX: 0")
        self._status_tx = QLabel("TX: 0")
        self._status_log = QLabel("")

        self._statusbar.addWidget(self._status_connection)
        self._statusbar.addWidget(self._status_port)
        self._statusbar.addWidget(self._status_baud)
        self._statusbar.addPermanentWidget(self._status_log)
        self._statusbar.addPermanentWidget(self._status_rx)
        self._statusbar.addPermanentWidget(self._status_tx)

    def _setup_shortcuts(self):
        """키보드 단축키 설정"""
        # Ctrl+F: 검색
        QShortcut(QKeySequence("Ctrl+F"), self, self._toggle_search)
        # F3: 다음 검색
        QShortcut(QKeySequence("F3"), self, lambda: self._search.find_next())
        # Shift+F3: 이전 검색
        QShortcut(QKeySequence("Shift+F3"), self, lambda: self._search.find_prev())

    def _connect_signals(self):
        """시그널 연결"""
        # 사이드바 시그널
        self._sidebar.connect_requested.connect(self._on_connect)
        self._sidebar.disconnect_requested.connect(lambda: self._on_disconnect(manual=True))
        self._sidebar.log_stop_requested.connect(self._on_log_stop)
        self._sidebar.clear_requested.connect(self._clear_terminal)

    # === 시리얼 연결 ===

    def _on_connect(self, settings: dict):
        """시리얼 포트 연결"""
        # LOG_DIR 확인 - 미설정시 다이얼로그
        if not self._ensure_log_dir():
            return

        try:
            self._reconnect_timer.stop()
            self._manual_disconnect = False

            self._serial.connect(
                port=settings["port"],
                baudrate=settings["baudrate"],
                databits=settings["databits"],
                parity=settings["parity"],
                stopbits=settings["stopbits"],
            )

            # 연결 설정 저장 (자동 재연결용)
            self._last_settings = settings.copy()

            # 수신 스레드 시작
            reader = self._serial.start_reading()
            reader.data_received.connect(self._on_data_received)
            reader.error_occurred.connect(self._on_serial_error)
            reader.start()

            # UI 업데이트
            self._sidebar.set_connected_state(True)
            self._update_statusbar_style(True)
            self._status_connection.setText("🟢 연결됨")
            self._status_port.setText(f"📡 {settings['port']}")
            self._status_baud.setText(f"⚡ {settings['baudrate']} bps")
            self._rx_bytes = 0
            self._tx_bytes = 0
            self._update_byte_counts()

            self._terminal.append_system_message(
                f"연결됨: {settings['port']} @ {settings['baudrate']} bps\n"
            )

            self.setWindowTitle(f"{self.APP_TITLE} - {settings['port']}")

            # 연결 시 자동 로그 시작
            self._auto_start_logging()

        except Exception as e:
            QMessageBox.critical(self, "연결 오류", f"시리얼 포트 연결에 실패했습니다:\n{str(e)}")
            self._terminal.append_system_message(f"연결 실패: {str(e)}\n")

    def _ensure_log_dir(self) -> bool:
        """LOG_DIR 확인 및 설정. 성공 시 True 반환."""
        if self._log_dir and os.path.isdir(self._log_dir):
            return True

        from PyQt6.QtWidgets import QFileDialog
        dir_path = QFileDialog.getExistingDirectory(
            self, "로그 저장 디렉토리 선택"
        )
        if not dir_path:
            self._terminal.append_system_message(
                "로그 디렉토리를 지정해야 연결할 수 있습니다.\n"
            )
            return False

        # .env 파일에 저장
        self._log_dir = dir_path
        os.environ["LOG_DIR"] = dir_path
        set_key(self._env_path, "LOG_DIR", dir_path)
        self._terminal.append_system_message(f"로그 디렉토리 설정: {dir_path}\n")
        return True

    def _generate_log_filename(self) -> str:
        """로그 파일명 자동 생성: lnxterm_YYYYMMDD_HHMMSS.log"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(self._log_dir, f"lnxterm_{timestamp}.log")

    def _auto_start_logging(self):
        """연결 시 자동 로그 시작"""
        if self._log.is_logging:
            return
        if self._log_dir:
            log_path = self._generate_log_filename()
            self._on_log_start(log_path)

    def _on_disconnect(self, manual: bool = True):
        """시리얼 포트 연결 해제"""
        port_name = self._serial.port_name
        self._serial.disconnect()

        self._sidebar.set_connected_state(False)
        self._update_statusbar_style(False)
        self._status_connection.setText("⚫ 연결 안됨")
        self._status_port.setText("")
        self._status_baud.setText("")

        self._terminal.append_system_message(f"연결 해제: {port_name}\n")
        self.setWindowTitle(self.APP_TITLE)

        if manual:
            # 수동 해제: 재연결 안 함, 로그 중지
            self._manual_disconnect = True
            self._reconnect_timer.stop()
            self._on_log_stop()
        else:
            # 비정상 끊김: 자동 재연결 시도
            if self._auto_reconnect and self._last_settings:
                self._terminal.append_system_message("3초 후 자동 재연결 시도...\n")
                self._status_connection.setText("🟡 재연결 대기")
                self._reconnect_timer.start()

    def _try_reconnect(self):
        """자동 재연결 시도"""
        self._reconnect_timer.stop()
        if self._manual_disconnect or not self._last_settings:
            return

        self._terminal.append_system_message("재연결 시도 중...\n")
        try:
            self._on_connect(self._last_settings)
        except Exception:
            # 실패 시 다시 3초 후 재시도
            self._terminal.append_system_message("재연결 실패, 3초 후 다시 시도...\n")
            self._reconnect_timer.start()

    def _on_data_received(self, data: bytes):
        """시리얼 데이터 수신"""
        self._rx_bytes += len(data)
        self._update_byte_counts()

        try:
            text = data.decode("utf-8", errors="replace")
        except Exception:
            text = data.decode("latin-1", errors="replace")

        # 터미널에 표시 및 완성된 라인 수집
        completed_lines = self._terminal.append_data(text, direction="rx")

        # 로그 파일에 기록
        for timestamp, line in completed_lines:
            self._log.write_line(line, timestamp)

    def _on_serial_error(self, error_msg: str):
        """시리얼 오류 처리 - 비정상 끊김, 자동 재연결 시도"""
        self._terminal.append_system_message(f"오류: {error_msg}\n")
        self._on_disconnect(manual=False)

    def _send_command(self):
        """명령 전송"""
        command = self._command_input.text()

        if not self._serial.is_connected():
            self._terminal.append_system_message("포트가 연결되지 않았습니다.\n")
            return

        try:
            # 명령 + LF 전송
            data = (command + "\n").encode("utf-8")
            sent = self._serial.write(data)
            self._tx_bytes += sent
            self._update_byte_counts()

            # 터미널에 표시 (빈 명령어도 표시)
            completed_lines = self._terminal.append_data(command + "\n", direction="tx")

            # 로그에 기록
            for timestamp, line in completed_lines:
                self._log.write_line(f"[TX] {line}", timestamp)

            # 히스토리에 추가 (빈 명령은 히스토리에 넣지 않음) 및 입력 클리어
            if command:
                self._command_input.add_to_history(command)
            self._command_input.clear()
            self._command_input.setFocus()

        except Exception as e:
            self._terminal.append_system_message(f"전송 오류: {str(e)}\n")

    # === 로그 관리 ===

    def _on_log_start_menu(self):
        """메뉴에서 로그 시작"""
        if not self._ensure_log_dir():
            return
        log_path = self._generate_log_filename()
        self._on_log_start(log_path)

    def _on_log_start(self, file_path: str):
        """로그 기록 시작"""
        try:
            self._log.start_logging(file_path)
            self._sidebar.set_logging_state(True)
            self._sidebar.set_actual_log_filename(os.path.basename(file_path))
            self._status_log.setText(f"📝 {os.path.basename(file_path)}")
            self._terminal.append_system_message(f"로그 기록 시작: {file_path}\n")
        except Exception as e:
            QMessageBox.critical(self, "로그 오류", f"로그 파일을 열 수 없습니다:\n{str(e)}")

    def _on_log_stop(self):
        """로그 기록 중지"""
        if self._log.is_logging:
            path = self._log.file_path
            self._log.stop_logging()
            self._sidebar.set_logging_state(False)
            self._status_log.setText("")
            self._terminal.append_system_message(f"로그 기록 종료: {path}\n")

    # === UI 도구 ===

    def _toggle_search(self):
        """검색 바 토글"""
        if self._search.isVisible():
            self._search.hide_search()
        else:
            self._search.show_search()

    def _toggle_sidebar(self):
        """사이드바 토글"""
        self._sidebar.setVisible(not self._sidebar.isVisible())

    def _clear_terminal(self):
        """터미널 클리어"""
        self._terminal.clear_terminal()
        self._terminal.append_system_message("터미널이 초기화되었습니다.\n")

    def _update_byte_counts(self):
        """RX/TX 바이트 카운트 업데이트"""
        self._status_rx.setText(f"RX: {self._format_bytes(self._rx_bytes)}")
        self._status_tx.setText(f"TX: {self._format_bytes(self._tx_bytes)}")

    def _update_statusbar_style(self, connected: bool):
        """상태바 스타일 변경"""
        if connected:
            self._statusbar.setStyleSheet(get_statusbar_connected_stylesheet())
        else:
            self._statusbar.setStyleSheet(get_statusbar_disconnected_stylesheet())

    @staticmethod
    def _format_bytes(count: int) -> str:
        """바이트 수를 가독성 있게 포맷"""
        if count < 1024:
            return f"{count} B"
        elif count < 1024 * 1024:
            return f"{count / 1024:.1f} KB"
        else:
            return f"{count / (1024 * 1024):.1f} MB"

    def _show_about(self):
        """정보 다이얼로그 표시"""
        QMessageBox.about(
            self,
            "LnxTerm 정보",
            "<h3>LnxTerm 시리얼 터미널</h3>"
            "<p>ST-Link V3 Mini 기반 임베디드 장치<br>"
            "디버그 및 로그 수집을 위한 시리얼 터미널</p>"
            "<p><b>기능:</b></p>"
            "<ul>"
            "<li>시리얼 포트 연결 및 명령 전송</li>"
            "<li>밀리초 타임스탬프 포함 로그 기록</li>"
            "<li>터미널 출력 검색</li>"
            "</ul>"
        )

    def closeEvent(self, event):
        """창 닫기 이벤트"""
        # 연결 해제
        if self._serial.is_connected():
            self._serial.disconnect()
        # 로그 종료
        if self._log.is_logging:
            self._log.stop_logging()
        event.accept()
