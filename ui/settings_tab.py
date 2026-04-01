"""
Tab Cài Đặt - Cấu hình giá phòng và các dịch vụ.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QDoubleSpinBox, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QCheckBox, QSpinBox, QTabWidget,
    QLineEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from database import db_manager
from utils.helpers import format_currency


class SettingsTab(QWidget):
    """Tab cài đặt."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Tiêu đề
        title = QLabel("⚙️ Cài Đặt")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #1565C0;")
        layout.addWidget(title)

        # Sub tabs
        self.sub_tabs = QTabWidget()
        self.sub_tabs.setStyleSheet("""
            QTabBar::tab {
                background: #e0e0e0; padding: 7px 16px;
                border-radius: 4px 4px 0 0; font-size: 12px;
            }
            QTabBar::tab:selected {
                background: #1976D2; color: white; font-weight: bold;
            }
        """)

        # Tab giá phòng
        rooms_tab = QWidget()
        self._setup_rooms_tab(rooms_tab)
        self.sub_tabs.addTab(rooms_tab, "🏠 Giá Phòng")

        # Tab giá dịch vụ
        service_tab = QWidget()
        self._setup_service_tab(service_tab)
        self.sub_tabs.addTab(service_tab, "💰 Giá Dịch Vụ")

        layout.addWidget(self.sub_tabs)

    def _setup_rooms_tab(self, parent):
        """Tab cài đặt giá phòng."""
        layout = QVBoxLayout(parent)
        layout.setSpacing(12)

        info_label = QLabel("📌 Thiết lập giá thuê từng phòng (có thể thay đổi bất cứ lúc nào)")
        info_label.setStyleSheet("""
            background: #e3f2fd;
            border: 1px solid #1976D2;
            border-radius: 5px;
            padding: 8px;
            color: #1565C0;
        """)
        layout.addWidget(info_label)

        self.rooms_table = QTableWidget()
        self.rooms_table.setColumnCount(4)
        self.rooms_table.setHorizontalHeaderLabels(["Phòng", "Mô Tả", "Giá Hiện Tại", "Giá Mới"])
        self.rooms_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.rooms_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.rooms_table.setStyleSheet("""
            QTableWidget { border: 1px solid #ddd; border-radius: 5px; font-size: 12px; }
            QHeaderView::section {
                background: #1976D2; color: white;
                padding: 8px; font-weight: bold; border: none;
            }
        """)
        layout.addWidget(self.rooms_table)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        save_rooms_btn = QPushButton("💾 Lưu Giá Phòng")
        save_rooms_btn.setStyleSheet("""
            QPushButton {
                background: #388E3C; color: white;
                border-radius: 5px; padding: 8px 18px;
                font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background: #2E7D32; }
        """)
        save_rooms_btn.clicked.connect(self._save_room_prices)
        btn_layout.addWidget(save_rooms_btn)
        layout.addLayout(btn_layout)

    def _setup_service_tab(self, parent):
        """Tab cài đặt giá dịch vụ."""
        layout = QVBoxLayout(parent)
        layout.setSpacing(12)

        # Tiền điện
        elec_group = QGroupBox("⚡ Tiền Điện")
        elec_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 13px; }")
        elec_layout = QFormLayout()

        self.electricity_price = QDoubleSpinBox()
        self.electricity_price.setRange(0, 100000)
        self.electricity_price.setSingleStep(100)
        self.electricity_price.setDecimals(0)
        self.electricity_price.setSuffix(" đ/số")
        elec_layout.addRow("Giá điện:", self.electricity_price)
        elec_group.setLayout(elec_layout)
        layout.addWidget(elec_group)

        # Tiền nước
        water_group = QGroupBox("💧 Tiền Nước")
        water_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 13px; }")
        water_layout = QFormLayout()

        self.water_price = QDoubleSpinBox()
        self.water_price.setRange(0, 1000000)
        self.water_price.setSingleStep(10000)
        self.water_price.setDecimals(0)
        self.water_price.setSuffix(" đ/người/tháng")
        water_layout.addRow("Giá nước/người:", self.water_price)
        water_group.setLayout(water_layout)
        layout.addWidget(water_group)

        # Tiền giặt
        laundry_group = QGroupBox("👕 Tiền Giặt")
        laundry_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 13px; }")
        laundry_layout = QFormLayout()

        self.laundry_1 = QDoubleSpinBox()
        self.laundry_1.setRange(0, 1000000)
        self.laundry_1.setSingleStep(10000)
        self.laundry_1.setDecimals(0)
        self.laundry_1.setSuffix(" đ")
        laundry_layout.addRow("1 người:", self.laundry_1)

        self.laundry_2 = QDoubleSpinBox()
        self.laundry_2.setRange(0, 1000000)
        self.laundry_2.setSingleStep(10000)
        self.laundry_2.setDecimals(0)
        self.laundry_2.setSuffix(" đ")
        laundry_layout.addRow("2 người:", self.laundry_2)

        self.laundry_3 = QDoubleSpinBox()
        self.laundry_3.setRange(0, 1000000)
        self.laundry_3.setSingleStep(10000)
        self.laundry_3.setDecimals(0)
        self.laundry_3.setSuffix(" đ")
        laundry_layout.addRow("3 người:", self.laundry_3)

        self.laundry_4plus = QDoubleSpinBox()
        self.laundry_4plus.setRange(0, 1000000)
        self.laundry_4plus.setSingleStep(10000)
        self.laundry_4plus.setDecimals(0)
        self.laundry_4plus.setSuffix(" đ")
        laundry_layout.addRow("4+ người:", self.laundry_4plus)

        laundry_group.setLayout(laundry_layout)
        layout.addWidget(laundry_group)

        # Dịch vụ khác
        other_group = QGroupBox("📦 Dịch Vụ Khác")
        other_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 13px; }")
        other_layout = QFormLayout()

        self.garbage_fee = QDoubleSpinBox()
        self.garbage_fee.setRange(0, 1000000)
        self.garbage_fee.setSingleStep(5000)
        self.garbage_fee.setDecimals(0)
        self.garbage_fee.setSuffix(" đ/tháng")
        other_layout.addRow("Tiền rác:", self.garbage_fee)

        self.internet_fee = QDoubleSpinBox()
        self.internet_fee.setRange(0, 1000000)
        self.internet_fee.setSingleStep(10000)
        self.internet_fee.setDecimals(0)
        self.internet_fee.setSuffix(" đ/tháng")
        other_layout.addRow("Tiền internet:", self.internet_fee)

        other_group.setLayout(other_layout)
        layout.addWidget(other_group)

        # Nút lưu
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        save_btn = QPushButton("💾 Lưu Cài Đặt Dịch Vụ")
        save_btn.setStyleSheet("""
            QPushButton {
                background: #388E3C; color: white;
                border-radius: 5px; padding: 8px 18px;
                font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background: #2E7D32; }
        """)
        save_btn.clicked.connect(self._save_service_settings)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

        layout.addStretch()

    def refresh_data(self):
        """Làm mới dữ liệu."""
        # Tải giá phòng
        rooms = db_manager.get_all_rooms()
        self.rooms_table.setRowCount(0)
        self._room_spins = []

        for room in rooms:
            row = self.rooms_table.rowCount()
            self.rooms_table.insertRow(row)

            self.rooms_table.setItem(row, 0, QTableWidgetItem(room["room_number"]))
            self.rooms_table.setItem(row, 1, QTableWidgetItem(room.get("description", "") or ""))
            self.rooms_table.setItem(row, 2, QTableWidgetItem(format_currency(room["price"])))

            price_spin = QDoubleSpinBox()
            price_spin.setRange(0, 100000000)
            price_spin.setSingleStep(100000)
            price_spin.setDecimals(0)
            price_spin.setSuffix(" đ")
            price_spin.setValue(room["price"])
            self.rooms_table.setCellWidget(row, 3, price_spin)
            self.rooms_table.setRowHeight(row, 45)

            self._room_spins.append({"room_id": room["id"], "spin": price_spin, "row": row})

        # Tải giá dịch vụ
        self.electricity_price.setValue(float(db_manager.get_setting("electricity_price", "3500")))
        self.water_price.setValue(float(db_manager.get_setting("water_price_per_person", "50000")))
        self.laundry_1.setValue(float(db_manager.get_setting("laundry_1_person", "30000")))
        self.laundry_2.setValue(float(db_manager.get_setting("laundry_2_person", "40000")))
        self.laundry_3.setValue(float(db_manager.get_setting("laundry_3_person", "50000")))
        self.laundry_4plus.setValue(float(db_manager.get_setting("laundry_4plus_person", "60000")))
        self.garbage_fee.setValue(float(db_manager.get_setting("garbage_fee", "0")))
        self.internet_fee.setValue(float(db_manager.get_setting("internet_fee", "0")))

    def _save_room_prices(self):
        """Lưu giá phòng."""
        try:
            for data in self._room_spins:
                new_price = data["spin"].value()
                db_manager.update_room_price(data["room_id"], new_price)

                # Cập nhật cột giá hiện tại
                current_item = self.rooms_table.item(data["row"], 2)
                if current_item:
                    current_item.setText(format_currency(new_price))

            QMessageBox.information(self, "Thành công", "Đã lưu giá phòng!")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu: {e}")

    def _save_service_settings(self):
        """Lưu cài đặt dịch vụ."""
        try:
            db_manager.update_setting("electricity_price", str(int(self.electricity_price.value())))
            db_manager.update_setting("water_price_per_person", str(int(self.water_price.value())))
            db_manager.update_setting("laundry_1_person", str(int(self.laundry_1.value())))
            db_manager.update_setting("laundry_2_person", str(int(self.laundry_2.value())))
            db_manager.update_setting("laundry_3_person", str(int(self.laundry_3.value())))
            db_manager.update_setting("laundry_4plus_person", str(int(self.laundry_4plus.value())))
            db_manager.update_setting("garbage_fee", str(int(self.garbage_fee.value())))
            db_manager.update_setting("internet_fee", str(int(self.internet_fee.value())))

            QMessageBox.information(self, "Thành công", "Đã lưu cài đặt dịch vụ!")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu: {e}")
