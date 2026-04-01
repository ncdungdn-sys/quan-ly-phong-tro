"""
Tab Ghi Chép Giặt - Quản lý tiền giặt theo phòng.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSpinBox, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from database import db_manager
from utils.helpers import format_currency, get_current_month_year, calculate_laundry


class LaundryTab(QWidget):
    """Tab ghi chép giặt."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Tiêu đề
        title = QLabel("👕 Ghi Chép Giặt")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #1565C0;")
        layout.addWidget(title)

        # Chọn tháng/năm
        month_layout = QHBoxLayout()
        month_layout.addWidget(QLabel("Tháng:"))
        self.month_spin = QSpinBox()
        self.month_spin.setRange(1, 12)
        month, year = get_current_month_year()
        self.month_spin.setValue(month)
        self.month_spin.setFixedWidth(60)
        month_layout.addWidget(self.month_spin)

        month_layout.addWidget(QLabel("Năm:"))
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2020, 2050)
        self.year_spin.setValue(year)
        self.year_spin.setFixedWidth(80)
        month_layout.addWidget(self.year_spin)

        load_btn = QPushButton("📋 Tải dữ liệu")
        load_btn.setStyleSheet("background: #1976D2; color: white; border-radius: 5px; padding: 6px 12px;")
        load_btn.clicked.connect(self.refresh_data)
        month_layout.addWidget(load_btn)

        month_layout.addStretch()
        layout.addLayout(month_layout)

        # Bảng giá tham khảo
        info_label = QLabel("📌 Bảng giá: 1 người: 30.000đ | 2 người: 40.000đ | 3 người: 50.000đ | 4+ người: 60.000đ")
        info_label.setStyleSheet("""
            background: #fff3e0;
            border: 1px solid #ff9800;
            border-radius: 5px;
            padding: 6px 12px;
            color: #e65100;
            font-size: 12px;
        """)
        layout.addWidget(info_label)

        # Bảng
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Phòng", "Số Người Hiện Tại", "Số Người Giặt", "Tiền Giặt", "Trạng Thái", "Lưu"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.table.setColumnWidth(5, 80)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                gridline-color: #eee;
                font-size: 12px;
            }
            QHeaderView::section {
                background: #7B1FA2;
                color: white;
                padding: 8px;
                font-weight: bold;
                border: none;
            }
        """)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        save_all_btn = QPushButton("💾 Lưu Tất Cả")
        save_all_btn.setStyleSheet("""
            QPushButton {
                background: #388E3C; color: white;
                border-radius: 5px; padding: 7px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background: #2E7D32; }
        """)
        save_all_btn.clicked.connect(self._save_all)
        btn_layout.addWidget(save_all_btn)
        layout.addLayout(btn_layout)

    def refresh_data(self):
        """Làm mới dữ liệu."""
        month = self.month_spin.value()
        year = self.year_spin.value()

        rooms = db_manager.get_all_rooms()
        self.table.setRowCount(0)
        self._row_data = []

        for room in rooms:
            if room["status"] == "empty":
                continue

            residents = db_manager.get_residents_by_room(room["id"], active_only=True)
            num_people = len(residents)

            row = self.table.rowCount()
            self.table.insertRow(row)

            # Lấy dữ liệu hiện tại
            record = db_manager.get_laundry_record(room["id"], month, year)

            # Phòng
            room_item = QTableWidgetItem(room["room_number"])
            room_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, room_item)

            # Số người hiện tại
            current_people_item = QTableWidgetItem(f"{num_people} người")
            current_people_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, current_people_item)

            # Số người giặt (spinbox)
            people_spin = QSpinBox()
            people_spin.setRange(0, 20)
            people_spin.setValue(record["num_people"] if record else num_people)
            self.table.setCellWidget(row, 2, people_spin)

            # Tiền giặt
            amount_item = QTableWidgetItem()
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 3, amount_item)

            # Trạng thái
            status_item = QTableWidgetItem("✅ Đã ghi" if record else "⬜ Chưa ghi")
            status_item.setTextAlignment(Qt.AlignCenter)
            if record:
                status_item.setForeground(Qt.darkGreen)
            self.table.setItem(row, 4, status_item)

            # Nút lưu
            save_btn = QPushButton("💾")
            save_btn.setStyleSheet("""
                QPushButton {
                    background: #1976D2; color: white;
                    border-radius: 4px; font-size: 11px;
                }
                QPushButton:hover { background: #1565C0; }
            """)
            save_btn.clicked.connect(lambda _, r=row, rid=room["id"]: self._save_row(r, rid))
            self.table.setCellWidget(row, 5, save_btn)
            self.table.setRowHeight(row, 45)

            self._row_data.append({"room_id": room["id"], "row": row})

            # Tính tự động
            people_spin.valueChanged.connect(lambda val, r=row: self._recalculate_row(r))
            self._recalculate_row(row)

    def _recalculate_row(self, row):
        """Tính lại tiền giặt."""
        people_spin = self.table.cellWidget(row, 2)
        if not people_spin:
            return
        num_people = people_spin.value()
        amount = calculate_laundry(num_people)
        amount_item = self.table.item(row, 3)
        if amount_item:
            amount_item.setText(format_currency(amount))

    def _save_row(self, row, room_id):
        """Lưu một hàng."""
        month = self.month_spin.value()
        year = self.year_spin.value()

        people_spin = self.table.cellWidget(row, 2)
        if not people_spin:
            return

        num_people = people_spin.value()
        amount = calculate_laundry(num_people)

        try:
            db_manager.save_laundry_record(room_id, month, year, num_people, amount)
            status_item = self.table.item(row, 4)
            if status_item:
                status_item.setText("✅ Đã ghi")
                status_item.setForeground(Qt.darkGreen)
            QMessageBox.information(self, "Thành công", "Đã lưu ghi chép giặt!")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu: {e}")

    def _save_all(self):
        """Lưu tất cả."""
        month = self.month_spin.value()
        year = self.year_spin.value()

        for data in self._row_data:
            row = data["row"]
            room_id = data["room_id"]

            people_spin = self.table.cellWidget(row, 2)
            if not people_spin:
                continue

            num_people = people_spin.value()
            amount = calculate_laundry(num_people)

            try:
                db_manager.save_laundry_record(room_id, month, year, num_people, amount)
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", f"Không thể lưu phòng {room_id}: {e}")

        QMessageBox.information(self, "Thành công", "Đã lưu tất cả ghi chép giặt!")
        self.refresh_data()
