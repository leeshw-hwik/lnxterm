"""
VS Code Dark+ 테마 스타일 정의
"""

# VS Code Dark+ 색상 팔레트
COLORS = {
    "bg_dark": "#1e1e1e",        # 메인 배경
    "bg_sidebar": "#252526",      # 사이드바 배경
    "bg_input": "#3c3c3c",        # 입력 필드 배경
    "bg_hover": "#2a2d2e",        # 호버 배경
    "bg_active": "#37373d",       # 활성 항목 배경
    "bg_selection": "#264f78",    # 선택 배경
    "bg_search": "#613a14",       # 검색 하이라이트
    "bg_search_current": "#9e6a03",  # 현재 검색 하이라이트
    "border": "#3c3c3c",          # 테두리
    "border_focus": "#007acc",    # 포커스 테두리

    "text_primary": "#d4d4d4",    # 기본 텍스트
    "text_secondary": "#858585",  # 보조 텍스트
    "text_disabled": "#5a5a5a",   # 비활성 텍스트
    "text_link": "#3794ff",       # 링크

    "accent": "#007acc",          # 주요 강조 (버튼, 상태바)
    "accent_hover": "#1b8ad4",    # 강조 호버
    "accent_active": "#0062a3",   # 강조 활성

    "success": "#4ec9b0",         # 성공 / 연결됨
    "warning": "#cca700",         # 경고
    "error": "#f44747",           # 오류 / 연결 해제
    "info": "#75beff",            # 정보

    "terminal_green": "#4ec9b0",  # 터미널 수신 텍스트
    "terminal_yellow": "#dcdcaa", # 타임스탬프
    "terminal_blue": "#569cd6",   # 송신 텍스트
    "terminal_red": "#f44747",    # 에러 텍스트
    "terminal_white": "#d4d4d4",  # 일반 텍스트

    "scrollbar_bg": "#1e1e1e",
    "scrollbar_handle": "#424242",
    "scrollbar_handle_hover": "#4f4f4f",

    "statusbar_bg": "#007acc",
    "statusbar_text": "#ffffff",
    "statusbar_disconnected_bg": "#6c6c6c",
}


def get_main_stylesheet():
    """메인 애플리케이션 QSS 스타일시트 반환"""
    c = COLORS
    return f"""
    /* === 전역 기본 === */
    QMainWindow {{
        background-color: {c['bg_dark']};
        color: {c['text_primary']};
    }}

    QWidget {{
        background-color: {c['bg_dark']};
        color: {c['text_primary']};
        font-family: 'Noto Sans KR', 'Segoe UI', 'Ubuntu', sans-serif;
        font-size: 13px;
    }}

    /* === 메뉴바 === */
    QMenuBar {{
        background-color: {c['bg_sidebar']};
        color: {c['text_primary']};
        border-bottom: 1px solid {c['border']};
        padding: 2px 0px;
    }}

    QMenuBar::item {{
        padding: 4px 10px;
        border-radius: 3px;
    }}

    QMenuBar::item:selected {{
        background-color: {c['bg_hover']};
    }}

    QMenu {{
        background-color: {c['bg_sidebar']};
        color: {c['text_primary']};
        border: 1px solid {c['border']};
        padding: 4px 0px;
    }}

    QMenu::item {{
        padding: 6px 30px 6px 20px;
    }}

    QMenu::item:selected {{
        background-color: {c['accent']};
    }}

    QMenu::separator {{
        height: 1px;
        background-color: {c['border']};
        margin: 4px 10px;
    }}

    /* === 사이드바 / 패널 === */
    QFrame#sidebar {{
        background-color: {c['bg_sidebar']};
        border-right: 1px solid {c['border']};
    }}

    /* === 라벨 === */
    QLabel {{
        color: {c['text_primary']};
        background-color: transparent;
    }}

    QLabel#sectionTitle {{
        color: {c['text_secondary']};
        font-size: 11px;
        font-weight: bold;
        text-transform: uppercase;
        padding: 8px 0px 4px 0px;
    }}

    /* === 콤보박스 === */
    QComboBox {{
        background-color: {c['bg_input']};
        color: {c['text_primary']};
        border: 1px solid {c['border']};
        border-radius: 3px;
        padding: 5px 8px;
        min-height: 22px;
    }}

    QComboBox:hover {{
        border-color: {c['border_focus']};
    }}

    QComboBox:focus {{
        border-color: {c['border_focus']};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {c['bg_sidebar']};
        color: {c['text_primary']};
        border: 1px solid {c['border']};
        selection-background-color: {c['accent']};
    }}

    /* === 버튼 === */
    QPushButton {{
        background-color: {c['accent']};
        color: white;
        border: none;
        border-radius: 3px;
        padding: 6px 14px;
        font-weight: 500;
        min-height: 24px;
    }}

    QPushButton:hover {{
        background-color: {c['accent_hover']};
    }}

    QPushButton:pressed {{
        background-color: {c['accent_active']};
    }}

    QPushButton:disabled {{
        background-color: {c['bg_input']};
        color: {c['text_disabled']};
    }}

    QPushButton#disconnectBtn {{
        background-color: {c['error']};
    }}

    QPushButton#disconnectBtn:hover {{
        background-color: #d73a3a;
    }}

    QPushButton#secondaryBtn {{
        background-color: {c['bg_input']};
        color: {c['text_primary']};
        border: 1px solid {c['border']};
    }}

    QPushButton#secondaryBtn:hover {{
        background-color: {c['bg_hover']};
    }}

    /* === 입력 필드 === */
    QLineEdit {{
        background-color: {c['bg_input']};
        color: {c['text_primary']};
        border: 1px solid {c['border']};
        border-radius: 3px;
        padding: 5px 8px;
        selection-background-color: {c['bg_selection']};
    }}

    QLineEdit:focus {{
        border-color: {c['border_focus']};
    }}

    /* === 체크박스 === */
    QCheckBox {{
        color: {c['text_primary']};
        spacing: 6px;
        background-color: transparent;
    }}

    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 3px;
        border: 1px solid {c['border']};
        background-color: {c['bg_input']};
    }}

    QCheckBox::indicator:checked {{
        background-color: {c['accent']};
        border-color: {c['accent']};
    }}

    /* === 스크롤바 === */
    QScrollBar:vertical {{
        background-color: {c['scrollbar_bg']};
        width: 12px;
        margin: 0;
    }}

    QScrollBar::handle:vertical {{
        background-color: {c['scrollbar_handle']};
        min-height: 30px;
        border-radius: 6px;
        margin: 2px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {c['scrollbar_handle_hover']};
    }}

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QScrollBar:horizontal {{
        background-color: {c['scrollbar_bg']};
        height: 12px;
        margin: 0;
    }}

    QScrollBar::handle:horizontal {{
        background-color: {c['scrollbar_handle']};
        min-width: 30px;
        border-radius: 6px;
        margin: 2px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background-color: {c['scrollbar_handle_hover']};
    }}

    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    /* === 상태바 === */
    QStatusBar {{
        background-color: {c['statusbar_bg']};
        color: {c['statusbar_text']};
        border-top: none;
        font-size: 12px;
    }}

    QStatusBar::item {{
        border: none;
    }}

    QStatusBar QLabel {{
        color: {c['statusbar_text']};
        padding: 2px 8px;
    }}

    /* === 스플리터 === */
    QSplitter::handle {{
        background-color: {c['border']};
    }}

    QSplitter::handle:horizontal {{
        width: 7px;
    }}

    QSplitter::handle:vertical {{
        height: 7px;
    }}

    /* === 툴팁 === */
    QToolTip {{
        background-color: {c['bg_sidebar']};
        color: {c['text_primary']};
        border: 1px solid {c['border']};
        padding: 4px 8px;
    }}

    /* === 그룹박스 === */
    QGroupBox {{
        background-color: transparent;
        border: 1px solid {c['border']};
        border-radius: 4px;
        margin-top: 12px;
        padding-top: 16px;
        font-weight: bold;
        color: {c['text_secondary']};
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 6px;
        color: {c['text_secondary']};
        font-size: 11px;
    }}

    QGroupBox#logGroup {{
        margin-top: 8px;
        padding-top: 8px;
    }}
    """


def get_terminal_stylesheet():
    """터미널 위젯 스타일시트 반환"""
    c = COLORS
    return f"""
    QPlainTextEdit {{
        background-color: {c['bg_dark']};
        color: {c['terminal_white']};
        font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', 'Courier New', monospace;
        font-size: 13px;
        border: none;
        padding: 8px;
        selection-background-color: {c['bg_selection']};
    }}
    """


def get_command_input_stylesheet():
    """명령 입력바 스타일시트 반환"""
    c = COLORS
    return f"""
    QLineEdit {{
        background-color: {c['bg_input']};
        color: {c['text_primary']};
        font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', 'Courier New', monospace;
        font-size: 13px;
        border: 1px solid {c['border']};
        border-radius: 0px;
        padding: 6px 10px;
        selection-background-color: {c['bg_selection']};
    }}

    QLineEdit:focus {{
        border-color: {c['border_focus']};
    }}
    """


def get_search_widget_stylesheet():
    """검색 위젯 스타일시트 반환"""
    c = COLORS
    return f"""
    QFrame#searchFrame {{
        background-color: {c['bg_sidebar']};
        border: 1px solid {c['border']};
        border-top: 2px solid {c['accent']};
        border-radius: 0px;
    }}

    QLineEdit#searchInput {{
        background-color: {c['bg_input']};
        color: {c['text_primary']};
        border: 1px solid {c['border']};
        border-radius: 3px;
        padding: 4px 8px;
        font-size: 13px;
    }}

    QLineEdit#searchInput:focus {{
        border-color: {c['border_focus']};
    }}

    QLabel#matchCount {{
        color: {c['text_secondary']};
        font-size: 12px;
        background-color: transparent;
    }}

    QPushButton#searchNavBtn {{
        background-color: transparent;
        color: {c['text_primary']};
        border: none;
        border-radius: 3px;
        padding: 4px 8px;
        font-size: 14px;
        min-height: 20px;
        min-width: 24px;
    }}

    QPushButton#searchNavBtn:hover {{
        background-color: {c['bg_hover']};
    }}

    QPushButton#searchCloseBtn {{
        background-color: transparent;
        color: {c['text_secondary']};
        border: none;
        border-radius: 3px;
        padding: 4px 6px;
        font-size: 16px;
        min-height: 20px;
        min-width: 20px;
    }}

    QPushButton#searchCloseBtn:hover {{
        background-color: {c['bg_hover']};
        color: {c['text_primary']};
    }}
    """


def get_statusbar_disconnected_stylesheet():
    """연결 해제 상태 상태바 스타일시트"""
    c = COLORS
    return f"""
    QStatusBar {{
        background-color: {c['statusbar_disconnected_bg']};
        color: {c['statusbar_text']};
    }}
    QStatusBar QLabel {{
        color: {c['statusbar_text']};
    }}
    """


def get_statusbar_connected_stylesheet():
    """연결 상태 상태바 스타일시트"""
    c = COLORS
    return f"""
    QStatusBar {{
        background-color: {c['statusbar_bg']};
        color: {c['statusbar_text']};
    }}
    QStatusBar QLabel {{
        color: {c['statusbar_text']};
    }}
    """
