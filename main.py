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
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from main_window import MainWindow


def main():
    # High DPI 지원
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("LnxTerm")
    app.setApplicationVersion("1.8.2")
    app.setOrganizationName("LnxTerm")

    # 기본 폰트 설정
    font = QFont("Noto Sans KR", 10)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)

    # 메인 윈도우 생성 및 표시
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
