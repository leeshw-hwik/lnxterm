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
from PyQt6.QtGui import QAction, QActionGroup, QShortcut, QKeySequence, QFont
from PyQt6.QtCore import Qt, QTimer, QSettings

from serial_manager import SerialManager
from log_manager import LogManager
from terminal_widget import TerminalWidget
from search_widget import SearchWidget
from sidebar_widget import SidebarWidget
from i18n import normalize_language, tr
from styles import (
    COLORS,
    get_main_stylesheet, get_command_input_stylesheet,
    get_statusbar_connected_stylesheet, get_statusbar_disconnected_stylesheet
)


class CommandInput(QLineEdit):
    """명령 입력 위젯 (히스토리 기능 포함)"""

    def __init__(self, parent=None, language: str = "ko"):
        super().__init__(parent)
        self._language = normalize_language(language)
        self.setStyleSheet(get_command_input_stylesheet())
        self.setPlaceholderText(tr(self._language, "command.placeholder"))

        self._history: list[str] = []
        self._history_index: int = -1
        self._max_history: int = 100

    def set_language(self, language: str):
        self._language = normalize_language(language)
        self.setPlaceholderText(tr(self._language, "command.placeholder"))

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

    APP_VERSION = "v1.8.5"
    DEFAULT_RECONNECT_INTERVAL_MS = 3000
    ENV_RECONNECT_INTERVAL_MS = "RECONNECT_INTERVAL_MS"
    ENV_RECONNECT_INTERVAL_SEC = "RECONNECT_INTERVAL_SEC"

    def __init__(self):
        super().__init__()
        self._settings = QSettings("LnxTerm", "LnxTerm")
        self._language = normalize_language(self._settings.value("language", "en", type=str))
        self._app_title = tr(self._language, "app.title")
        self.setWindowTitle(self._app_title)
        self.setMinimumSize(1000, 650)
        self.resize(1280, 768)

        # .env 파일 로드 (실행 파일 디렉토리 우선)
        self._env_path = self._resolve_env_path()
        load_dotenv(self._env_path, override=True)
        self._log_dir = os.path.abspath(
            os.path.expanduser(os.environ.get("LOG_DIR", "").strip())
        ) if os.environ.get("LOG_DIR", "").strip() else ""
        self._persistent_log_path: str = ""
        self._reconnect_interval_ms = self._resolve_reconnect_interval_ms()

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
        self._reconnect_timer.setInterval(self._reconnect_interval_ms)
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

        # 환경 변수 사전 설정 로드
        self._sidebar.load_configs_from_env()

        self._apply_language()

        # 초기 상태
        self._update_statusbar_style(False)
        self._terminal.append_system_message(tr(self._language, "msg.app_started"))

        # LOG_DIR 확인
        if self._log_dir:
            self._terminal.append_system_message(
                tr(self._language, "msg.log_dir", path=self._log_dir)
            )
        else:
            self._terminal.append_system_message(tr(self._language, "msg.log_dir_not_set"))
        self._terminal.append_system_message(
            tr(self._language, "msg.reconnect_interval", interval=self._get_reconnect_delay_text())
        )
        self._terminal.append_system_message(
            tr(self._language, "msg.env_path", path=self._env_path)
        )

        self._terminal.append_system_message(tr(self._language, "msg.select_port"))

    def _setup_menu_bar(self):
        """메뉴바 구성"""
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)

        # 파일 메뉴
        self._file_menu = menubar.addMenu("")

        self._log_start_action = QAction("", self)
        self._log_start_action.setShortcut("Ctrl+L")
        self._log_start_action.triggered.connect(self._on_log_start_menu)
        self._file_menu.addAction(self._log_start_action)

        self._log_stop_action = QAction("", self)
        self._log_stop_action.triggered.connect(self._on_log_stop)
        self._file_menu.addAction(self._log_stop_action)

        self._file_menu.addSeparator()

        self._update_env_action = QAction("", self)
        self._update_env_action.setShortcut("Ctrl+S")
        self._update_env_action.triggered.connect(self._on_update_env_configs)
        self._file_menu.addAction(self._update_env_action)

        self._file_menu.addSeparator()

        self._exit_action = QAction("", self)
        self._exit_action.setShortcut("Ctrl+Q")
        self._exit_action.triggered.connect(self.close)
        self._file_menu.addAction(self._exit_action)

        # 편집 메뉴
        self._edit_menu = menubar.addMenu("")

        self._find_action = QAction("", self)
        self._find_action.setShortcut("Ctrl+F")
        self._find_action.triggered.connect(self._toggle_search)
        self._edit_menu.addAction(self._find_action)

        self._edit_menu.addSeparator()

        self._clear_action = QAction("", self)
        self._clear_action.setShortcut("Ctrl+Shift+C")
        self._clear_action.triggered.connect(self._clear_terminal)
        self._edit_menu.addAction(self._clear_action)

        # 보기 메뉴
        self._view_menu = menubar.addMenu("")

        self._sidebar_action = QAction("", self)
        self._sidebar_action.setShortcut("Ctrl+B")
        self._sidebar_action.triggered.connect(self._toggle_sidebar)
        self._view_menu.addAction(self._sidebar_action)

        self._refresh_action = QAction("", self)
        self._refresh_action.setShortcut("F5")
        self._refresh_action.triggered.connect(lambda: self._sidebar.refresh_ports())
        self._view_menu.addAction(self._refresh_action)

        self._language_menu = menubar.addMenu("")
        self._language_action_group = QActionGroup(self)
        self._language_action_group.setExclusive(True)

        self._lang_ko_action = QAction("", self, checkable=True)
        self._lang_ko_action.triggered.connect(lambda checked: checked and self._set_language("ko"))
        self._language_action_group.addAction(self._lang_ko_action)
        self._language_menu.addAction(self._lang_ko_action)

        self._lang_en_action = QAction("", self, checkable=True)
        self._lang_en_action.triggered.connect(lambda checked: checked and self._set_language("en"))
        self._language_action_group.addAction(self._lang_en_action)
        self._language_menu.addAction(self._lang_en_action)

        # 도움말 메뉴
        self._help_menu = menubar.addMenu("")

        self._about_action = QAction("", self)
        self._about_action.triggered.connect(self._show_about)
        self._help_menu.addAction(self._about_action)

    def _setup_central_widget(self):
        """중앙 위젯 구성"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 좌우 영역 분할 (마우스로 크기 조절 가능)
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setChildrenCollapsible(False)
        self._splitter.setHandleWidth(7)
        main_layout.addWidget(self._splitter, 1)

        # 사이드바
        self._sidebar = SidebarWidget(language=self._language)
        self._splitter.addWidget(self._sidebar)

        # 오른쪽 영역 (터미널 + 검색 + 입력)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # 검색 위젯
        self._terminal = TerminalWidget()
        self._search = SearchWidget(self._terminal, language=self._language)
        right_layout.addWidget(self._search)

        # 터미널
        right_layout.addWidget(self._terminal, 1)

        # 명령 입력 바
        input_frame = QFrame()
        input_frame.setStyleSheet(
            f"background-color: {COLORS['bg_sidebar']}; border-top: 1px solid {COLORS['border']};"
        )
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(8, 4, 8, 4)
        input_layout.setSpacing(8)

        prompt_label = QLabel("❯")
        prompt_label.setStyleSheet(
            f"color: {COLORS['accent']}; font-size: 16px; font-weight: bold; background-color: transparent;"
        )
        input_layout.addWidget(prompt_label)

        self._command_input = CommandInput(language=self._language)
        self._command_input.returnPressed.connect(self._send_command)
        input_layout.addWidget(self._command_input, 1)

        # 전송 버튼
        self._send_btn = QPushButton(tr(self._language, "button.send"))
        self._send_btn.setFixedHeight(30)
        self._send_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._send_btn.clicked.connect(self._send_command)
        input_layout.addWidget(self._send_btn)

        right_layout.addWidget(input_frame)

        self._splitter.addWidget(right_panel)
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)
        self._splitter.setSizes([300, 980])

    def _setup_status_bar(self):
        """상태바 구성"""
        self._statusbar = self.statusBar()

        self._status_connection = QLabel(tr(self._language, "status.disconnected"))
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
        # Ctrl+F: 검색 (메뉴 액션과 중복되므로 제거)
        # QShortcut(QKeySequence("Ctrl+F"), self, self._toggle_search)
        
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
        self._sidebar.send_command_requested.connect(self.send_serial_command)

        # 터미널 엔터 시 커맨드 입력창으로 포커스
        self._terminal.return_pressed.connect(self._command_input.setFocus)

    def _set_language(self, language: str):
        normalized = normalize_language(language)
        if normalized == self._language:
            return
        self._language = normalized
        self._settings.setValue("language", normalized)
        self._apply_language()

    def _apply_language(self):
        self._app_title = tr(self._language, "app.title")
        self._file_menu.setTitle(tr(self._language, "menu.file"))
        self._edit_menu.setTitle(tr(self._language, "menu.edit"))
        self._view_menu.setTitle(tr(self._language, "menu.view"))
        self._help_menu.setTitle(tr(self._language, "menu.help"))
        self._language_menu.setTitle(tr(self._language, "menu.language"))

        self._log_start_action.setText(tr(self._language, "action.log_start"))
        self._log_stop_action.setText(tr(self._language, "action.log_stop"))
        self._update_env_action.setText(tr(self._language, "action.update_env"))
        self._exit_action.setText(tr(self._language, "action.exit"))
        self._find_action.setText(tr(self._language, "action.find"))
        self._clear_action.setText(tr(self._language, "action.clear_terminal"))
        self._sidebar_action.setText(tr(self._language, "action.toggle_sidebar"))
        self._refresh_action.setText(tr(self._language, "action.refresh_ports"))
        self._about_action.setText(tr(self._language, "action.about"))
        self._lang_ko_action.setText(tr(self._language, "action.lang_ko"))
        self._lang_en_action.setText(tr(self._language, "action.lang_en"))

        self._lang_ko_action.setChecked(self._language == "ko")
        self._lang_en_action.setChecked(self._language == "en")

        self._command_input.set_language(self._language)
        self._send_btn.setText(tr(self._language, "button.send"))
        self._search.set_language(self._language)
        self._sidebar.set_language(self._language)
        self._update_connection_status_text()

        if self._serial.is_connected() and self._serial.port_name:
            self.setWindowTitle(f"{self._app_title} - {self._serial.port_name}")
        else:
            self.setWindowTitle(self._app_title)

    def _update_connection_status_text(self):
        if self._serial.is_connected():
            self._status_connection.setText(tr(self._language, "status.connected"))
        elif self._reconnect_timer.isActive():
            self._status_connection.setText(tr(self._language, "status.reconnecting"))
        else:
            self._status_connection.setText(tr(self._language, "status.disconnected"))

    # === 시리얼 연결 ===

    def _on_connect(self, settings: dict, silent: bool = False) -> bool:
        """시리얼 포트 연결. silent=True이면 다이얼로그 없이 경고만 출력."""
        # LOG_DIR 확인 - 미설정시 다이얼로그
        if not self._ensure_log_dir():
            return False

        try:
            self._terminal.set_max_lines(
                settings.get("max_lines", TerminalWidget.DEFAULT_MAX_LINES)
            )
            self._reconnect_timer.stop()
            self._manual_disconnect = False

            # 포트 점유 프로세스 확인
            port = settings["port"]
            in_use = SerialManager.check_port_in_use(port)
            if in_use:
                procs_info = "\n".join(
                    [f"  • {p['name']} (PID: {p['pid']})" for p in in_use]
                )
                self._terminal.append_system_message(
                    tr(
                        self._language,
                        "msg.port_in_use_warning_terminal",
                        port=port,
                        procs=procs_info,
                    )
                )
                if not silent:
                    reply = QMessageBox.warning(
                        self,
                        tr(self._language, "dialog.port_in_use.title"),
                        tr(
                            self._language,
                            "dialog.port_in_use.body",
                            port=port,
                            procs=procs_info,
                        ),
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No,
                    )
                    if reply != QMessageBox.StandardButton.Yes:
                        self._terminal.append_system_message(tr(self._language, "msg.connect_canceled"))
                        return False

            self._serial.connect(
                port=port,
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
            self._update_connection_status_text()
            self._status_port.setText(f"📡 {settings['port']}")
            self._status_baud.setText(f"⚡ {settings['baudrate']} bps")
            self._rx_bytes = 0
            self._tx_bytes = 0
            self._update_byte_counts()

            self._terminal.append_system_message(
                tr(
                    self._language,
                    "msg.connected",
                    port=settings["port"],
                    baudrate=settings["baudrate"],
                )
            )

            self.setWindowTitle(f"{self._app_title} - {settings['port']}")

            # 연결 시 자동 로그 시작
            self._auto_start_logging()
            return True

        except Exception as e:
            QMessageBox.critical(
                self,
                tr(self._language, "dialog.connect_error.title"),
                tr(self._language, "dialog.connect_error.body", error=str(e)),
            )
            self._terminal.append_system_message(
                tr(self._language, "msg.connect_failed", error=str(e))
            )
            return False

    def _ensure_log_dir(self) -> bool:
        """LOG_DIR 확인 및 설정. 성공 시 True 반환."""
        if self._log_dir:
            normalized = os.path.abspath(os.path.expanduser(self._log_dir))
            try:
                os.makedirs(normalized, exist_ok=True)
            except OSError:
                pass
            if os.path.isdir(normalized):
                self._log_dir = normalized
                os.environ["LOG_DIR"] = normalized
                return True

        from PyQt6.QtWidgets import QFileDialog
        dir_path = QFileDialog.getExistingDirectory(
            self, tr(self._language, "dialog.select_log_dir")
        )
        if not dir_path:
            self._terminal.append_system_message(
                tr(self._language, "msg.log_dir_required")
            )
            return False

        # .env 파일에 저장
        self._log_dir = os.path.abspath(os.path.expanduser(dir_path))
        os.environ["LOG_DIR"] = self._log_dir
        set_key(self._env_path, "LOG_DIR", self._log_dir)
        self._terminal.append_system_message(
            tr(self._language, "msg.log_dir_set", path=self._log_dir)
        )
        return True

    def _resolve_env_path(self) -> str:
        """실행 환경에 맞는 .env 경로 결정."""
        candidate_paths: list[str] = []
        if getattr(sys, "frozen", False):
            candidate_paths.append(
                os.path.join(os.path.dirname(os.path.abspath(sys.executable)), ".env")
            )
        candidate_paths.append(os.path.join(os.getcwd(), ".env"))
        candidate_paths.append(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        )

        unique_candidates = []
        for path in candidate_paths:
            normalized = os.path.abspath(path)
            if normalized not in unique_candidates:
                unique_candidates.append(normalized)

        for path in unique_candidates:
            if os.path.isfile(path):
                return path

        # 기존 파일이 없으면 실행 파일 폴더(배포 환경) 또는 소스 폴더(개발 환경)에 생성
        if getattr(sys, "frozen", False):
            return os.path.join(
                os.path.dirname(os.path.abspath(sys.executable)), ".env"
            )
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

    def _resolve_reconnect_interval_ms(self) -> int:
        """환경변수에서 자동 재연결 주기를 읽어 ms 단위로 반환."""
        raw_ms = os.environ.get(self.ENV_RECONNECT_INTERVAL_MS, "").strip()
        parsed_ms = self._parse_positive_milliseconds(raw_ms)
        if parsed_ms is not None:
            return parsed_ms

        raw_sec = os.environ.get(self.ENV_RECONNECT_INTERVAL_SEC, "").strip()
        parsed_sec_ms = self._parse_positive_seconds_to_ms(raw_sec)
        if parsed_sec_ms is not None:
            return parsed_sec_ms

        return self.DEFAULT_RECONNECT_INTERVAL_MS

    @staticmethod
    def _parse_positive_milliseconds(raw_value: str) -> int | None:
        """양의 밀리초 문자열을 int로 변환. 실패 시 None."""
        if not raw_value:
            return None
        try:
            value = int(float(raw_value))
        except ValueError:
            return None
        return value if value > 0 else None

    @staticmethod
    def _parse_positive_seconds_to_ms(raw_value: str) -> int | None:
        """양의 초 문자열을 ms(int)로 변환. 실패 시 None."""
        if not raw_value:
            return None
        try:
            value = float(raw_value)
        except ValueError:
            return None
        if value <= 0:
            return None
        return int(value * 1000)

    def _get_reconnect_delay_text(self) -> str:
        """자동 재연결 주기를 화면 표시용 텍스트로 변환."""
        if self._reconnect_interval_ms % 1000 == 0:
            return tr(
                self._language,
                "time.seconds.integer",
                value=self._reconnect_interval_ms // 1000,
            )
        return tr(
            self._language,
            "time.seconds.float",
            value=self._reconnect_interval_ms / 1000,
        )

    def _generate_log_filename(self) -> str:
        """로그 파일명 자동 생성: lnxterm_YYYYMMDD_HHMMSS.log"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(self._log_dir, f"lnxterm_{timestamp}.log")

    def _auto_start_logging(self):
        """연결 시 자동 로그 시작"""
        if self._log.is_logging:
            return
        if self._log_dir:
            if not self._persistent_log_path:
                self._persistent_log_path = self._generate_log_filename()
            self._on_log_start(self._persistent_log_path)

    def _on_disconnect(self, manual: bool = True):
        """시리얼 포트 연결 해제"""
        port_name = self._serial.port_name
        self._serial.disconnect()

        self._sidebar.set_connected_state(False)
        self._update_statusbar_style(False)
        self._status_port.setText("")
        self._status_baud.setText("")

        self._terminal.append_system_message(
            tr(self._language, "msg.disconnected", port=port_name)
        )
        self.setWindowTitle(self._app_title)

        self._on_log_stop(clear_display=False)
        if manual:
            # 수동 해제: 재연결 안 함, 로그 중지
            self._manual_disconnect = True
            self._reconnect_timer.stop()
            self._update_connection_status_text()
        else:
            # 비정상 끊김: 자동 재연결 시도
            if self._auto_reconnect and self._last_settings:
                self._terminal.append_system_message(
                    tr(
                        self._language,
                        "msg.auto_reconnect_after",
                        delay=self._get_reconnect_delay_text(),
                    )
                )
                self._reconnect_timer.start()
        self._update_connection_status_text()

    def _try_reconnect(self):
        """자동 재연결 시도"""
        self._reconnect_timer.stop()
        if self._manual_disconnect or not self._last_settings:
            self._update_connection_status_text()
            return

        self._terminal.append_system_message(tr(self._language, "msg.reconnect_trying"))
        reconnected = self._on_connect(self._last_settings, silent=True)
        if not reconnected:
            # 실패 시 설정된 주기 후 재시도
            self._terminal.append_system_message(
                tr(
                    self._language,
                    "msg.reconnect_failed",
                    delay=self._get_reconnect_delay_text(),
                )
            )
            self._reconnect_timer.start()
            self._update_connection_status_text()

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
            self._sidebar.process_log_line_for_counters(line, timestamp)
            self._sidebar.process_log_line_for_automation(line)
            self._log.write_line(line, timestamp)

    def _on_serial_error(self, error_msg: str):
        """시리얼 오류 처리 - 비정상 끊김, 자동 재연결 시도"""
        self._terminal.append_system_message(
            tr(self._language, "msg.error_prefix", error=error_msg)
        )
        self._on_disconnect(manual=False)

    def _send_command(self):
        """GUI 입력창의 명령 전송"""
        command = self._command_input.text()
        
        # 빈 명령이라도 일단 전송 시도(엔터 역할)
        self.send_serial_command(command)

        # 히스토리 추가 및 입력 클리어
        if command:
            self._command_input.add_to_history(command)
        self._command_input.clear()
        self._command_input.setFocus()

    def send_serial_command(self, content: str, interval_ms: int = 0):
        """
        시리얼 명령 전송 (단일/멀티라인 지원, 간격 지원).
        content에 포함된 각 라인을 순차적으로 전송.
        interval_ms > 0 이면 각 라인 전송 사이 지연.
        """
        if not content:
            lines = [""]
        else:
            lines = content.splitlines()
        
        if not lines:
            lines = [""]

        if not self._serial.is_connected():
            self._terminal.append_system_message(tr(self._language, "msg.port_not_connected"))
            return

        if interval_ms <= 0:
            try:
                for line in lines:
                    self._send_line_logic(line)
                self._update_byte_counts()
            except Exception as e:
                self._terminal.append_system_message(
                    tr(self._language, "msg.send_error", error=str(e))
                )
        else:
            self._send_lines_delayed(lines, interval_ms)

    def _send_line_logic(self, line: str):
        """단일 라인 전송 로직 (로그/터미널 처리 포함)"""
        data = (line + "\n").encode("utf-8")
        sent = self._serial.write(data)
        self._tx_bytes += sent
        
        completed_lines = self._terminal.append_data(line + "\n", direction="tx")
        
        for timestamp, log_line in completed_lines:
            tx_line = f"[TX] {log_line}"
            self._log.write_line(tx_line, timestamp)

    def _send_lines_delayed(self, lines: list, interval_ms: int):
        """지연 시간을 두고 순차 전송"""
        if not lines:
            self._update_byte_counts()
            return
        
        try:
            line = lines[0]
            self._send_line_logic(line)
            
            remaining = lines[1:]
            if remaining:
                QTimer.singleShot(interval_ms, lambda: self._send_lines_delayed(remaining, interval_ms))
            else:
                self._update_byte_counts()
        except Exception as e:
            self._terminal.append_system_message(
                tr(self._language, "msg.send_error_delayed", error=str(e))
            )

    # === 로그 관리 ===
    # === 로그 관리 ===

    def _on_log_start_menu(self):
        """메뉴에서 로그 시작"""
        if not self._ensure_log_dir():
            return
        if not self._persistent_log_path:
            self._persistent_log_path = self._generate_log_filename()
        log_path = self._persistent_log_path
        self._on_log_start(log_path)

    def _on_log_start(self, file_path: str):
        """로그 기록 시작"""
        try:
            if not self._persistent_log_path:
                self._persistent_log_path = file_path
            self._log.start_logging(file_path)
            self._sidebar.set_stats_output_from_logfile(file_path)
            self._sidebar.set_logging_state(True)
            self._sidebar.set_log_started_time(self._log.started_at)
            self._sidebar.set_actual_log_filename(file_path)
            self._status_log.setText(f"📝 {os.path.basename(file_path)}")
            self._terminal.append_system_message(
                tr(self._language, "msg.log_start", path=file_path)
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                tr(self._language, "dialog.log_error.title"),
                tr(self._language, "dialog.log_error.body", error=str(e)),
            )

    def _on_log_stop(self, clear_display: bool = True):
        """로그 기록 중지"""
        if self._log.is_logging:
            path = self._log.file_path
            self._log.stop_logging()
            self._sidebar.set_logging_state(False, clear_display=clear_display)
            if clear_display:
                self._status_log.setText("")
            self._terminal.append_system_message(
                tr(self._language, "msg.log_stop", path=path)
            )

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
        self._terminal.append_system_message(tr(self._language, "msg.terminal_cleared"))

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
            tr(self._language, "about.title"),
            tr(self._language, "about.body", version=self.APP_VERSION),
        )

    def _on_update_env_configs(self):
        """환경 변수 업데이트 실행"""
        success = self._sidebar.save_configs_to_env(self._env_path)
        if success:
            self._terminal.append_system_message(tr(self._language, "msg.env_updated"))
            QMessageBox.information(
                self,
                tr(self._language, "dialog.done.title"),
                tr(self._language, "dialog.done.body"),
            )
        else:
            mode = os.environ.get("AUTO_LOAD_MODE", "CONFIRM")
            if mode == "IGNORE":
                QMessageBox.warning(
                    self,
                    tr(self._language, "dialog.update_unavailable.title"),
                    tr(self._language, "dialog.update_unavailable.body", mode=mode),
                )
            else:
                QMessageBox.warning(
                    self,
                    tr(self._language, "dialog.failed.title"),
                    tr(self._language, "dialog.failed.body"),
                )

    def closeEvent(self, event):
        """창 닫기 이벤트"""
        # 연결 해제
        if self._serial.is_connected():
            self._serial.disconnect()
        # 로그 종료
        if self._log.is_logging:
            self._log.stop_logging()
        
        # 현재 설정 저장
        # 모드가 IGNORE면 내부에서 False 반환하며 저장 안 함.
        self._sidebar.save_configs_to_env(self._env_path)
            
        event.accept()
