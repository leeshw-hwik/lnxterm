#!/usr/bin/env python3
"""
LnxTerm - 시리얼 터미널 애플리케이션
ST-Link V3 Mini를 이용한 임베디드 장치 디버그 및 로그 수집
"""

import sys
import os

# 프로젝트 루트를 모듈 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QPalette, QColor
from PyQt6.QtCore import Qt

from main_window import MainWindow


def main():
    # High DPI 지원
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("LnxTerm")
    app.setApplicationVersion("1.10.0")
    app.setOrganizationName("LnxTerm")

    # 기본 폰트 설정
    font = QFont("Noto Sans KR", 10)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)

    # Fusion 스타일 및 다크 테마 적용 (VS Code 스타일)
    app.setStyle("Fusion")
    
    dark_palette = QPalette()
    # Window background (VS Code sidebar/activity bar greyish)
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    # Base background (Editor/Terminal background - usually darker)
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(30, 30, 30))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    # Highlight color (VS Code blue-ish)
    dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    
    app.setPalette(dark_palette)

    # 메인 윈도우 생성 및 표시
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
