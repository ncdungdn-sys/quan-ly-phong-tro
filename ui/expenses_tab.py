"""
Tab Quản Lý Chi Phí - Chi phí chung và chi phí theo phòng.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QLineEdit, QDoubleSpinBox,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QMessageBox, QSpinBox, QTabWidget, QGroupBox,
    QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from database import db_manager
from utils.helpers import format_currency, get_current_month_year


class AddExpenseDialog(QDialog):
    """Dialog thêm chi phí chung."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Thêm Chi Phí Chung")
        self.setMinimumWidth(400)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("VD: Sửa mái tôn, vệ sinh chung...")
        form.addRow("Mô tả:*", self.desc_edit)

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 100000000)
        self.amount_spin.setSingleStep(10000)
        self.amount_spin.setSuffix(" đ")
        self.amount_spin.setDecimals(0)
        form.addRow("Số tiền:*", self.amount_spin)

        self.category_combo = QComboBox()
        self.category_combo.addItems(["Sửa chữa", "Bảo trì", "Vệ sinh", "Tiện ích", "Khác"])
        form.addRow("Loại:", self.category_combo)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        save_btn = QPushButton("💾 Lưu")
        save_btn.setStyleSheet("background: #388E3C; color: white; border-radius: 5px; padding: 6px 14px;")
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("❌ Hủy")
        cancel_btn.setStyleSheet("background: #D32F2F; color: white; border-radius: 5px; padding: 6px 14px;")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def get_data(self):
        return {
            "description": self.desc_edit.text().strip(),
            "amount": self.amount_spin.value(),
            "category": self.category_combo.currentText(),
        }

    def accept(self):
        if not self.desc_edit.text().strip():
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập mô tả!")
            return
        if self.amount_spin.value() <= 0:
            QMessageBox.warning(self, "Lỗi", "Số tiền phải lớn hơn 0!")
            return
        super().accept()


class AddRoomExpenseDialog(QDialog):
    """Dialog thêm chi phí theo phòng."""

    def __init__(self, parent=None, rooms=None):
        super().__init__(parent)
        self.rooms = rooms or []
        self.setWindowTitle("Thêm Chi Phí Theo Phòng")
        self.setMinimumWidth(420)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.room_combo = QComboBox()
        for room in self.rooms:
            self.room_combo.addItem(room["room_number"], room["id"])
        form.addRow("Phòng:*", self.room_combo)

        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("VD: Sửa điều hòa, thay bóng đèn...")
        form.addRow("Mô tả:*", self.desc_edit)

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 100000000)
        self.amount_spin.setSingleStep(10000)
        self.amount_spin.setSuffix(" đ")
        self.amount_spin.setDecimals(0)
        form.addRow("Số tiền:*", self.amount_spin)

        # Ai chịu?
        paid_by_group = QGroupBox("Ai chịu chi phí?")
        paid_by_layout = QHBoxLayout()
        self.owner_radio = QRadioButton("Chủ nhà chịu")
        self.owner_radio.setChecked(True)
        self.resident_radio = QRadioButton("Cư dân chịu (cộng vào hóa đơn)")
        paid_by_layout.addWidget(self.owner_radio)
        paid_by_layout.addWidget(self.resident_radio)
        paid_by_group.setLayout(paid_by_layout)
        form.addRow("", paid_by_group)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        save_btn = QPushButton("💾 Lưu")
        save_btn.setStyleSheet("background: #388E3C; color: white; border-radius: 5px; padding: 6px 14px;")
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("❌ Hủy")
        cancel_btn.setStyleSheet("background: #D32F2F; color: white; border-radius: 5px; padding: 6px 14px;")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def get_data(self):
        return {
            "room_id": self.room_combo.currentData(),
            "description": self.desc_edit.text().strip(),
            "amount": self.amount_spin.value(),
            "paid_by": "owner" if self.owner_radio.isChecked() else "resident",
        }

    def accept(self):
        if not self.desc_edit.text().strip():
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập mô tả!")
            return
        if self.amount_spin.value() <= 0:
            QMessageBox.warning(self, "Lỗi", "Số tiền phải lớn hơn 0!")
            return
        super().accept()


class ExpensesTab(QWidget):
    """Tab quản lý chi phí."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Tiêu đề
        title = QLabel("💰 Quản Lý Chi Phí")
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

        load_btn = QPushButton("📋 Tải")
        load_btn.setStyleSheet("background: #1976D2; color: white; border-radius: 5px; padding: 6px 12px;")
        load_btn.clicked.connect(self.refresh_data)
        month_layout.addWidget(load_btn)

        month_layout.addStretch()
        layout.addLayout(month_layout)

        # Sub-tabs
        self.sub_tabs = QTabWidget()
        self.sub_tabs.setStyleSheet("""
            QTabBar::tab {
                background: #e0e0e0; padding: 6px 14px;
                border-radius: 4px 4px 0 0; font-size: 12px;
            }
            QTabBar::tab:selected {
                background: #D32F2F; color: white; font-weight: bold;
            }
        """)

        # Tab 1: Chi phí chung
        general_tab = QWidget()
        self._setup_general_expenses(general_tab)
        self.sub_tabs.addTab(general_tab, "🏢 Chi Phí Chung")

        # Tab 2: Chi phí phòng
        room_tab = QWidget()
        self._setup_room_expenses(room_tab)
        self.sub_tabs.addTab(room_tab, "🏠 Chi Phí Phòng")

        layout.addWidget(self.sub_tabs)

        # Tổng kết
        self.total_label = QLabel()
        self.total_label.setStyleSheet("""
            background: #fff3e0;
            border: 1px solid #ff9800;
            border-radius: 5px;
            padding: 8px;
            font-size: 13px;
            font-weight: bold;
        """)
        layout.addWidget(self.total_label)

    def _setup_general_expenses(self, parent):
        """Thiết lập tab chi phí chung."""
        layout = QVBoxLayout(parent)

        # Nút thêm
        add_layout = QHBoxLayout()
        add_layout.addStretch()
        add_btn = QPushButton("➕ Thêm Chi Phí")
        add_btn.setStyleSheet("background: #388E3C; color: white; border-radius: 5px; padding: 6px 14px; font-weight: bold;")
        add_btn.clicked.connect(self._add_general_expense)
        add_layout.addWidget(add_btn)
        layout.addLayout(add_layout)

        self.general_table = QTableWidget()
        self.general_table.setColumnCount(5)
        self.general_table.setHorizontalHeaderLabels(["ID", "Mô Tả", "Số Tiền", "Loại", "Xóa"])
        self.general_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.general_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.general_table.setColumnWidth(0, 50)
        self.general_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.general_table.setColumnWidth(4, 60)
        self.general_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.general_table.setStyleSheet("""
            QTableWidget { border: 1px solid #ddd; border-radius: 5px; font-size: 12px; }
            QHeaderView::section {
                background: #D32F2F; color: white;
                padding: 7px; font-weight: bold; border: none;
            }
        """)
        layout.addWidget(self.general_table)

        self.general_total_label = QLabel("Tổng: 0đ")
        self.general_total_label.setStyleSheet("color: #D32F2F; font-weight: bold; font-size: 13px;")
        layout.addWidget(self.general_total_label)

    def _setup_room_expenses(self, parent):
        """Thiết lập tab chi phí phòng."""
        layout = QVBoxLayout(parent)

        add_layout = QHBoxLayout()
        add_layout.addStretch()
        add_btn = QPushButton("➕ Thêm Chi Phí Phòng")
        add_btn.setStyleSheet("background: #7B1FA2; color: white; border-radius: 5px; padding: 6px 14px; font-weight: bold;")
        add_btn.clicked.connect(self._add_room_expense)
        add_layout.addWidget(add_btn)
        layout.addLayout(add_layout)

        self.room_table = QTableWidget()
        self.room_table.setColumnCount(6)
        self.room_table.setHorizontalHeaderLabels(["ID", "Phòng", "Mô Tả", "Số Tiền", "Người Chịu", "Xóa"])
        self.room_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.room_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.room_table.setColumnWidth(0, 50)
        self.room_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.room_table.setColumnWidth(5, 60)
        self.room_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.room_table.setStyleSheet("""
            QTableWidget { border: 1px solid #ddd; border-radius: 5px; font-size: 12px; }
            QHeaderView::section {
                background: #7B1FA2; color: white;
                padding: 7px; font-weight: bold; border: none;
            }
        """)
        layout.addWidget(self.room_table)

        self.room_total_label = QLabel("Tổng: 0đ | Chủ chịu: 0đ | Cư dân chịu: 0đ")
        self.room_total_label.setStyleSheet("color: #7B1FA2; font-weight: bold; font-size: 12px;")
        layout.addWidget(self.room_total_label)

    def refresh_data(self):
        """Làm mới dữ liệu."""
        month = self.month_spin.value()
        year = self.year_spin.value()

        # Chi phí chung
        expenses = db_manager.get_expenses_by_month(month, year)
        self.general_table.setRowCount(0)
        total_general = 0
        for exp in expenses:
            row = self.general_table.rowCount()
            self.general_table.insertRow(row)
            self.general_table.setItem(row, 0, QTableWidgetItem(str(exp["id"])))
            self.general_table.setItem(row, 1, QTableWidgetItem(exp["description"]))
            amount_item = QTableWidgetItem(format_currency(exp["amount"]))
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.general_table.setItem(row, 2, amount_item)
            self.general_table.setItem(row, 3, QTableWidgetItem(exp["category"] or ""))

            del_btn = QPushButton("🗑️")
            del_btn.setStyleSheet("background: #D32F2F; color: white; border-radius: 3px;")
            del_btn.clicked.connect(lambda _, eid=exp["id"]: self._delete_general_expense(eid))
            self.general_table.setCellWidget(row, 4, del_btn)
            self.general_table.setRowHeight(row, 38)
            total_general += exp["amount"]

        self.general_total_label.setText(f"Tổng chi phí chung: {format_currency(total_general)}")

        # Chi phí phòng
        room_expenses = db_manager.get_room_expenses_by_month(month, year)
        self.room_table.setRowCount(0)
        total_owner = 0
        total_resident = 0
        for exp in room_expenses:
            row = self.room_table.rowCount()
            self.room_table.insertRow(row)
            self.room_table.setItem(row, 0, QTableWidgetItem(str(exp["id"])))
            self.room_table.setItem(row, 1, QTableWidgetItem(exp.get("room_number", "")))
            self.room_table.setItem(row, 2, QTableWidgetItem(exp["description"]))
            amount_item = QTableWidgetItem(format_currency(exp["amount"]))
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.room_table.setItem(row, 3, amount_item)

            paid_by_text = "Chủ nhà" if exp["paid_by"] == "owner" else "Cư dân"
            paid_item = QTableWidgetItem(paid_by_text)
            if exp["paid_by"] == "resident":
                paid_item.setForeground(Qt.red)
            else:
                paid_item.setForeground(Qt.darkBlue)
            self.room_table.setItem(row, 4, paid_item)

            del_btn = QPushButton("🗑️")
            del_btn.setStyleSheet("background: #D32F2F; color: white; border-radius: 3px;")
            del_btn.clicked.connect(lambda _, eid=exp["id"]: self._delete_room_expense(eid))
            self.room_table.setCellWidget(row, 5, del_btn)
            self.room_table.setRowHeight(row, 38)

            if exp["paid_by"] == "owner":
                total_owner += exp["amount"]
            else:
                total_resident += exp["amount"]

        self.room_total_label.setText(
            f"Tổng: {format_currency(total_owner + total_resident)} | "
            f"Chủ chịu: {format_currency(total_owner)} | "
            f"Cư dân chịu: {format_currency(total_resident)}"
        )

        # Cập nhật tổng
        summary = db_manager.get_monthly_summary(month, year)
        self.total_label.setText(
            f"📊 Tổng chi phí tháng {month:02d}/{year}: "
            f"Chung: {format_currency(summary['total_expenses'])} | "
            f"Phòng (chủ chịu): {format_currency(summary['owner_expenses'])} | "
            f"Tổng: {format_currency(summary['total_cost'])}"
        )

    def _add_general_expense(self):
        """Thêm chi phí chung."""
        dialog = AddExpenseDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            month = self.month_spin.value()
            year = self.year_spin.value()
            try:
                db_manager.add_expense(month, year, data["description"], data["amount"], data["category"])
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể thêm: {e}")

    def _delete_general_expense(self, expense_id):
        """Xóa chi phí chung."""
        reply = QMessageBox.question(self, "Xác nhận", "Xóa chi phí này?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            db_manager.delete_expense(expense_id)
            self.refresh_data()

    def _add_room_expense(self):
        """Thêm chi phí phòng."""
        rooms = db_manager.get_all_rooms()
        dialog = AddRoomExpenseDialog(self, rooms=rooms)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            month = self.month_spin.value()
            year = self.year_spin.value()
            try:
                db_manager.add_room_expense(
                    data["room_id"], month, year,
                    data["description"], data["amount"], data["paid_by"]
                )
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể thêm: {e}")

    def _delete_room_expense(self, expense_id):
        """Xóa chi phí phòng."""
        reply = QMessageBox.question(self, "Xác nhận", "Xóa chi phí phòng này?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            db_manager.delete_room_expense(expense_id)
            self.refresh_data()
