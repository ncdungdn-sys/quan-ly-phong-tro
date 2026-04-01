"""
Entry point cho ứng dụng Quản Lý Phòng Trọ.
Chạy file này để khởi động ứng dụng.
"""
import sys
import os

# Thêm thư mục gốc vào Python path để import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication, QSplashScreen, QMessageBox
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor

from database.db_manager import init_database
from ui.main_window import MainWindow


def create_splash_screen():
    """Tạo màn hình chào (splash screen)."""
    pixmap = QPixmap(400, 250)
    pixmap.fill(QColor("#1565C0"))

    painter = QPainter(pixmap)
    painter.setPen(QColor("white"))

    font_title = QFont()
    font_title.setPointSize(24)
    font_title.setBold(True)
    painter.setFont(font_title)
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "🏠 Quản Lý Phòng Trọ")

    font_sub = QFont()
    font_sub.setPointSize(12)
    painter.setFont(font_sub)
    painter.drawText(
        0, 170, 400, 30,
        Qt.AlignHCenter,
        "Đang khởi động..."
    )
    painter.end()

    splash = QSplashScreen(pixmap)
    splash.setWindowFlags(Qt.SplashScreen | Qt.WindowStaysOnTopHint)
    return splash


def main():
    """Hàm main - khởi động ứng dụng."""
    app = QApplication(sys.argv)
    app.setApplicationName("Quản Lý Phòng Trọ")
    app.setOrganizationName("PhongTro")

    # Set font mặc định
    default_font = QFont()
    default_font.setFamily("Arial")
    default_font.setPointSize(10)
    app.setFont(default_font)

    # Style sheet toàn cục
    app.setStyleSheet("""
        QWidget {
            font-family: Arial, 'Segoe UI', sans-serif;
            font-size: 11px;
        }
        QToolTip {
            background-color: #1976D2;
            color: white;
            border: none;
            padding: 4px;
        }
        QScrollBar:vertical {
            width: 12px;
            background: #f5f5f5;
            border-radius: 6px;
        }
        QScrollBar::handle:vertical {
            background: #bbb;
            border-radius: 6px;
            min-height: 30px;
        }
        QScrollBar::handle:vertical:hover {
            background: #999;
        }
        QScrollBar:horizontal {
            height: 12px;
            background: #f5f5f5;
            border-radius: 6px;
        }
        QScrollBar::handle:horizontal {
            background: #bbb;
            border-radius: 6px;
        }
    """)

    # Khởi tạo database
    try:
        init_database()
        print("✅ Database đã khởi tạo thành công")
    except Exception as e:
        QMessageBox.critical(None, "Lỗi Database", f"Không thể khởi tạo database:\n{e}")
        sys.exit(1)

    # Tạo và hiển thị cửa sổ chính
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
