"""
Tab Dashboard - Hiển thị tổng quan tình trạng phòng trọ.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QPushButton, QScrollArea
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from datetime import datetime

from utils.helpers import format_currency, get_current_month_year
from database import db_manager


class StatCard(QFrame):
    """Card hiển thị một chỉ số thống kê."""

    def __init__(self, title, value, icon, color="#1976D2", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedHeight(110)
        self.setStyleSheet(f"""
            QFrame {{
                background: white;
                border-radius: 10px;
                border: 2px solid {color};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(5)

        # Icon và title
        header_layout = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("", 20))
        icon_label.setStyleSheet(f"color: {color}; border: none;")
        header_layout.addWidget(icon_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: #666; font-size: 12px; border: none;")
        layout.addWidget(title_label)

        # Value
        self.value_label = QLabel(str(value))
        value_font = QFont()
        value_font.setPointSize(18)
        value_font.setBold(True)
        self.value_label.setFont(value_font)
        self.value_label.setStyleSheet(f"color: {color}; border: none;")
        layout.addWidget(self.value_label)

    def update_value(self, value):
        """Cập nhật giá trị hiển thị."""
        self.value_label.setText(str(value))


class RoomStatusCard(QFrame):
    """Card hiển thị trạng thái một phòng."""

    def __init__(self, room_data, residents, parent=None):
        super().__init__(parent)
        self.room_data = room_data
        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedHeight(130)

        is_occupied = room_data["status"] == "occupied"
        border_color = "#4CAF50" if is_occupied else "#9E9E9E"
        bg_color = "#f1f8e9" if is_occupied else "#fafafa"

        self.setStyleSheet(f"""
            QFrame {{
                background: {bg_color};
                border-radius: 8px;
                border: 2px solid {border_color};
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(3)

        # Room number
        room_label = QLabel(f"🏠 {room_data['room_number']}")
        room_font = QFont()
        room_font.setPointSize(14)
        room_font.setBold(True)
        room_label.setFont(room_font)
        room_label.setStyleSheet(f"color: {border_color};")
        layout.addWidget(room_label)

        # Status
        status_text = "🟢 Có người ở" if is_occupied else "⚪ Trống"
        status_label = QLabel(status_text)
        status_label.setStyleSheet("font-size: 12px; color: #555;")
        layout.addWidget(status_label)

        # Price
        price_label = QLabel(f"💰 {format_currency(room_data['price'])}/tháng")
        price_label.setStyleSheet("font-size: 11px; color: #777;")
        layout.addWidget(price_label)

        # Residents
        if residents:
            names = ", ".join(r["full_name"] for r in residents[:2])
            if len(residents) > 2:
                names += f" +{len(residents)-2}"
            resident_label = QLabel(f"👤 {names}")
            resident_label.setStyleSheet("font-size: 11px; color: #555;")
            resident_label.setWordWrap(True)
            layout.addWidget(resident_label)
        else:
            layout.addWidget(QLabel(""))

        layout.addStretch()


class DashboardWidget(QWidget):
    """Widget Dashboard chính."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        """Thiết lập giao diện dashboard."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Tiêu đề
        title_layout = QHBoxLayout()
        title_label = QLabel("📊 Tổng Quan")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #1565C0;")
        title_layout.addWidget(title_label)

        title_layout.addStretch()

        month, year = get_current_month_year()
        self.month_label = QLabel(f"📅 Tháng {month:02d}/{year}")
        self.month_label.setStyleSheet("color: #666; font-size: 13px;")
        title_layout.addWidget(self.month_label)

        refresh_btn = QPushButton("🔄 Làm mới")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #1976D2;
                color: white;
                border-radius: 5px;
                padding: 5px 12px;
                font-size: 12px;
            }
            QPushButton:hover { background: #1565C0; }
        """)
        refresh_btn.clicked.connect(self.refresh_data)
        title_layout.addWidget(refresh_btn)

        main_layout.addLayout(title_layout)

        # Stats cards row 1
        stats_layout = QGridLayout()
        stats_layout.setSpacing(12)

        self.card_total_rooms = StatCard("Tổng Phòng", "7", "🏠", "#1976D2")
        self.card_occupied = StatCard("Phòng Có Người", "0", "🟢", "#4CAF50")
        self.card_empty = StatCard("Phòng Trống", "0", "⚪", "#9E9E9E")
        self.card_residents = StatCard("Cư Dân", "0", "👥", "#9C27B0")
        self.card_revenue = StatCard("Doanh Thu Tháng", "0đ", "💵", "#F57C00")
        self.card_paid = StatCard("Đã Thu", "0đ", "✅", "#388E3C")
        self.card_expenses = StatCard("Chi Phí", "0đ", "📤", "#D32F2F")
        self.card_profit = StatCard("Lợi Nhuận", "0đ", "📈", "#1565C0")

        stats_layout.addWidget(self.card_total_rooms, 0, 0)
        stats_layout.addWidget(self.card_occupied, 0, 1)
        stats_layout.addWidget(self.card_empty, 0, 2)
        stats_layout.addWidget(self.card_residents, 0, 3)
        stats_layout.addWidget(self.card_revenue, 1, 0)
        stats_layout.addWidget(self.card_paid, 1, 1)
        stats_layout.addWidget(self.card_expenses, 1, 2)
        stats_layout.addWidget(self.card_profit, 1, 3)

        main_layout.addLayout(stats_layout)

        # Room status grid
        rooms_title = QLabel("🏠 Trạng Thái Các Phòng")
        rooms_title_font = QFont()
        rooms_title_font.setPointSize(13)
        rooms_title_font.setBold(True)
        rooms_title.setFont(rooms_title_font)
        rooms_title.setStyleSheet("color: #1565C0; margin-top: 5px;")
        main_layout.addWidget(rooms_title)

        # Scroll area cho room cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.rooms_container = QWidget()
        self.rooms_layout = QGridLayout(self.rooms_container)
        self.rooms_layout.setSpacing(10)
        scroll.setWidget(self.rooms_container)
        main_layout.addWidget(scroll)

    def refresh_data(self):
        """Làm mới tất cả dữ liệu dashboard."""
        try:
            stats = db_manager.get_dashboard_stats()
            month, year = get_current_month_year()

            self.card_total_rooms.update_value(stats["total_rooms"])
            self.card_occupied.update_value(stats["occupied_rooms"])
            self.card_empty.update_value(stats["empty_rooms"])
            self.card_residents.update_value(stats["total_residents"])
            self.card_revenue.update_value(format_currency(stats["monthly_revenue"]))
            self.card_paid.update_value(format_currency(stats["monthly_paid"]))
            self.card_expenses.update_value(format_currency(stats["monthly_expenses"]))
            self.card_profit.update_value(format_currency(stats["monthly_profit"]))

            self.month_label.setText(f"📅 Tháng {month:02d}/{year}")

            # Cập nhật room cards
            self._refresh_rooms()

        except Exception as e:
            print(f"Lỗi refresh dashboard: {e}")

    def _refresh_rooms(self):
        """Làm mới grid các phòng."""
        # Xóa cards cũ
        while self.rooms_layout.count():
            item = self.rooms_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        rooms = db_manager.get_all_rooms()
        col_count = 4
        for i, room in enumerate(rooms):
            residents = db_manager.get_residents_by_room(room["id"], active_only=True)
            card = RoomStatusCard(room, residents)
            row, col = divmod(i, col_count)
            self.rooms_layout.addWidget(card, row, col)

        # Thêm khoảng trống
        self.rooms_layout.addWidget(QWidget(), len(rooms) // col_count + 1, 0)
