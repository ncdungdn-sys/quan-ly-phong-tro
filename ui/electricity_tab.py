"""
Tab Ghi Số Điện - Ghi và quản lý số điện từng phòng.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QDoubleSpinBox, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QMessageBox, QSpinBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from database import db_manager
from utils.helpers import format_currency, get_current_month_year, calculate_electricity


class ElectricityTab(QWidget):
    """Tab ghi số điện."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Tiêu đề
        title = QLabel("⚡ Ghi Số Điện")
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

        # Bảng ghi số điện
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Phòng", "Số Cũ", "Số Mới", "Số Dùng",
            "Đơn Giá", "Thành Tiền", "Đã Ghi", "Lưu"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Fixed)
        self.table.setColumnWidth(7, 80)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                gridline-color: #eee;
                font-size: 12px;
            }
            QHeaderView::section {
                background: #F57C00;
                color: white;
                padding: 8px;
                font-weight: bold;
                border: none;
            }
        """)
        layout.addWidget(self.table)

        # Thông tin giá điện
        info_layout = QHBoxLayout()
        self.price_label = QLabel()
        self.price_label.setStyleSheet("color: #666; font-size: 12px;")
        info_layout.addWidget(self.price_label)
        info_layout.addStretch()

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
        info_layout.addWidget(save_all_btn)
        layout.addLayout(info_layout)

    def refresh_data(self):
        """Làm mới dữ liệu."""
        month = self.month_spin.value()
        year = self.year_spin.value()

        price_per_unit = float(db_manager.get_setting("electricity_price", "3500"))
        self.price_label.setText(f"⚡ Giá điện: {format_currency(price_per_unit)}/số")

        rooms = db_manager.get_all_rooms()
        self.table.setRowCount(0)
        self._row_data = []

        for room in rooms:
            if room["status"] == "empty":
                continue

            row = self.table.rowCount()
            self.table.insertRow(row)

            # Lấy dữ liệu hiện tại nếu có
            reading = db_manager.get_electricity_reading(room["id"], month, year)
            last_reading = db_manager.get_last_electricity_reading(room["id"], month, year)

            old_val = 0
            new_val = 0
            if reading:
                old_val = reading["old_reading"]
                new_val = reading["new_reading"]
            elif last_reading:
                old_val = last_reading["new_reading"]

            # Phòng
            room_item = QTableWidgetItem(room["room_number"])
            room_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, room_item)

            # Số cũ (spinbox)
            old_spin = QDoubleSpinBox()
            old_spin.setRange(0, 999999)
            old_spin.setValue(old_val)
            old_spin.setDecimals(0)
            old_spin.setSuffix(" số")
            self.table.setCellWidget(row, 1, old_spin)

            # Số mới (spinbox)
            new_spin = QDoubleSpinBox()
            new_spin.setRange(0, 999999)
            new_spin.setValue(new_val)
            new_spin.setDecimals(0)
            new_spin.setSuffix(" số")
            self.table.setCellWidget(row, 2, new_spin)

            # Số dùng (computed)
            units_item = QTableWidgetItem()
            units_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, units_item)

            # Đơn giá
            price_item = QTableWidgetItem(format_currency(price_per_unit))
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 4, price_item)

            # Thành tiền
            amount_item = QTableWidgetItem()
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 5, amount_item)

            # Trạng thái đã ghi
            status_item = QTableWidgetItem("✅ Đã ghi" if reading else "⬜ Chưa ghi")
            status_item.setTextAlignment(Qt.AlignCenter)
            if reading:
                status_item.setForeground(Qt.darkGreen)
            self.table.setItem(row, 6, status_item)

            # Nút lưu
            save_btn = QPushButton("💾 Lưu")
            save_btn.setStyleSheet("""
                QPushButton {
                    background: #1976D2; color: white;
                    border-radius: 4px; font-size: 11px;
                }
                QPushButton:hover { background: #1565C0; }
            """)
            save_btn.clicked.connect(lambda _, r=row, rid=room["id"]: self._save_row(r, rid))
            self.table.setCellWidget(row, 7, save_btn)

            self.table.setRowHeight(row, 45)
            self._row_data.append({"room_id": room["id"], "row": row})

            # Kết nối tính tự động
            old_spin.valueChanged.connect(lambda _, r=row: self._recalculate_row(r))
            new_spin.valueChanged.connect(lambda _, r=row: self._recalculate_row(r))

            # Tính ngay
            self._recalculate_row(row)

    def _recalculate_row(self, row):
        """Tính lại số dùng và thành tiền cho một hàng."""
        old_spin = self.table.cellWidget(row, 1)
        new_spin = self.table.cellWidget(row, 2)
        if not old_spin or not new_spin:
            return

        old_val = old_spin.value()
        new_val = new_spin.value()
        units = max(0, new_val - old_val)

        price_per_unit = float(db_manager.get_setting("electricity_price", "3500"))
        amount = units * price_per_unit

        units_item = self.table.item(row, 3)
        if units_item:
            units_item.setText(f"{units:.0f} số")

        amount_item = self.table.item(row, 5)
        if amount_item:
            amount_item.setText(format_currency(amount))

    def _save_row(self, row, room_id):
        """Lưu một hàng."""
        month = self.month_spin.value()
        year = self.year_spin.value()

        old_spin = self.table.cellWidget(row, 1)
        new_spin = self.table.cellWidget(row, 2)
        if not old_spin or not new_spin:
            return

        old_val = old_spin.value()
        new_val = new_spin.value()

        if new_val < old_val:
            QMessageBox.warning(self, "Lỗi", "Số mới phải lớn hơn hoặc bằng số cũ!")
            return

        try:
            db_manager.save_electricity_reading(room_id, month, year, old_val, new_val)
            status_item = self.table.item(row, 6)
            if status_item:
                status_item.setText("✅ Đã ghi")
                status_item.setForeground(Qt.darkGreen)
            QMessageBox.information(self, "Thành công", "Đã lưu số điện!")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu: {e}")

    def _save_all(self):
        """Lưu tất cả hàng."""
        month = self.month_spin.value()
        year = self.year_spin.value()
        errors = []

        for data in self._row_data:
            row = data["row"]
            room_id = data["room_id"]

            old_spin = self.table.cellWidget(row, 1)
            new_spin = self.table.cellWidget(row, 2)
            if not old_spin or not new_spin:
                continue

            old_val = old_spin.value()
            new_val = new_spin.value()

            if new_val < old_val:
                room_item = self.table.item(row, 0)
                room_num = room_item.text() if room_item else f"Row {row}"
                errors.append(f"Phòng {room_num}: Số mới < số cũ!")
                continue

            try:
                db_manager.save_electricity_reading(room_id, month, year, old_val, new_val)
            except Exception as e:
                errors.append(str(e))

        if errors:
            QMessageBox.warning(self, "Một số lỗi", "\n".join(errors))
        else:
            QMessageBox.information(self, "Thành công", "Đã lưu tất cả số điện!")
            self.refresh_data()
