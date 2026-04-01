"""
Tab Quản Lý Cư Dân - CRUD cư dân.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QDateEdit,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QMessageBox, QSpinBox, QGroupBox, QFrame
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor

from database import db_manager
from utils.helpers import format_date, format_currency


BUTTON_STYLE = """
    QPushButton {
        border-radius: 5px;
        padding: 6px 14px;
        font-size: 12px;
        font-weight: bold;
    }
"""

PRIMARY_BTN = BUTTON_STYLE + """
    QPushButton { background: #1976D2; color: white; }
    QPushButton:hover { background: #1565C0; }
"""

SUCCESS_BTN = BUTTON_STYLE + """
    QPushButton { background: #388E3C; color: white; }
    QPushButton:hover { background: #2E7D32; }
"""

DANGER_BTN = BUTTON_STYLE + """
    QPushButton { background: #D32F2F; color: white; }
    QPushButton:hover { background: #B71C1C; }
"""

WARNING_BTN = BUTTON_STYLE + """
    QPushButton { background: #F57C00; color: white; }
    QPushButton:hover { background: #E65100; }
"""


class ResidentDialog(QDialog):
    """Dialog thêm/sửa cư dân."""

    def __init__(self, parent=None, resident=None, rooms=None):
        super().__init__(parent)
        self.resident = resident
        self.rooms = rooms or []
        self.setWindowTitle("Thêm Cư Dân" if not resident else "Sửa Thông Tin Cư Dân")
        self.setMinimumWidth(450)
        self.setModal(True)
        self._setup_ui()
        if resident:
            self._fill_data()

    def _setup_ui(self):
        """Thiết lập giao diện dialog."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        form = QFormLayout()
        form.setSpacing(10)

        # Phòng
        self.room_combo = QComboBox()
        for room in self.rooms:
            self.room_combo.addItem(
                f"{room['room_number']} - {format_currency(room['price'])}",
                room["id"]
            )
        form.addRow("Phòng:*", self.room_combo)

        # Họ tên
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Nhập họ tên đầy đủ")
        form.addRow("Họ tên:*", self.name_edit)

        # Tuổi
        self.age_spin = QSpinBox()
        self.age_spin.setRange(1, 100)
        self.age_spin.setValue(25)
        form.addRow("Tuổi:", self.age_spin)

        # CCCD
        self.id_card_edit = QLineEdit()
        self.id_card_edit.setPlaceholderText("Số CCCD/CMND")
        form.addRow("CCCD:", self.id_card_edit)

        # SĐT
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("Số điện thoại")
        form.addRow("SĐT:", self.phone_edit)

        # Ngày vào ở
        self.check_in_edit = QDateEdit()
        self.check_in_edit.setCalendarPopup(True)
        self.check_in_edit.setDate(QDate.currentDate())
        self.check_in_edit.setDisplayFormat("dd/MM/yyyy")
        form.addRow("Ngày vào:*", self.check_in_edit)

        # Ghi chú
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Ghi chú thêm...")
        self.notes_edit.setMaximumHeight(80)
        form.addRow("Ghi chú:", self.notes_edit)

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        save_btn = QPushButton("💾 Lưu")
        save_btn.setStyleSheet(SUCCESS_BTN)
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("❌ Hủy")
        cancel_btn.setStyleSheet(DANGER_BTN)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def _fill_data(self):
        """Điền dữ liệu vào form khi sửa."""
        r = self.resident
        # Chọn phòng
        for i in range(self.room_combo.count()):
            if self.room_combo.itemData(i) == r["room_id"]:
                self.room_combo.setCurrentIndex(i)
                break

        self.name_edit.setText(r.get("full_name", ""))
        self.age_spin.setValue(r.get("age", 25) or 25)
        self.id_card_edit.setText(r.get("id_card", "") or "")
        self.phone_edit.setText(r.get("phone", "") or "")
        self.notes_edit.setPlainText(r.get("notes", "") or "")

        check_in = r.get("check_in_date", "")
        if check_in:
            date = QDate.fromString(check_in, "yyyy-MM-dd")
            if date.isValid():
                self.check_in_edit.setDate(date)

    def get_data(self):
        """Lấy dữ liệu từ form."""
        return {
            "room_id": self.room_combo.currentData(),
            "full_name": self.name_edit.text().strip(),
            "age": self.age_spin.value(),
            "id_card": self.id_card_edit.text().strip(),
            "phone": self.phone_edit.text().strip(),
            "check_in_date": self.check_in_edit.date().toString("yyyy-MM-dd"),
            "notes": self.notes_edit.toPlainText().strip(),
        }

    def validate(self):
        """Kiểm tra dữ liệu hợp lệ."""
        data = self.get_data()
        if not data["full_name"]:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập họ tên!")
            self.name_edit.setFocus()
            return False
        if not data["room_id"]:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn phòng!")
            return False
        return True

    def accept(self):
        """Override accept để validate trước."""
        if self.validate():
            super().accept()


class ResidentsTab(QWidget):
    """Tab quản lý cư dân."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        """Thiết lập giao diện tab."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Tiêu đề và nút
        header = QHBoxLayout()
        title = QLabel("👥 Quản Lý Cư Dân")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #1565C0;")
        header.addWidget(title)

        header.addStretch()

        # Lọc theo phòng
        filter_label = QLabel("Lọc phòng:")
        header.addWidget(filter_label)
        self.room_filter = QComboBox()
        self.room_filter.setMinimumWidth(150)
        self.room_filter.currentIndexChanged.connect(self._apply_filter)
        header.addWidget(self.room_filter)

        add_btn = QPushButton("➕ Thêm Cư Dân")
        add_btn.setStyleSheet(SUCCESS_BTN)
        add_btn.clicked.connect(self._add_resident)
        header.addWidget(add_btn)

        layout.addLayout(header)

        # Bảng cư dân
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Phòng", "Họ Tên", "Tuổi", "CCCD", "SĐT",
            "Ngày Vào", "Ghi Chú", "Thao Tác"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 50)
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.Fixed)
        self.table.setColumnWidth(8, 180)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                gridline-color: #eee;
                font-size: 12px;
            }
            QHeaderView::section {
                background: #1976D2;
                color: white;
                padding: 8px;
                font-weight: bold;
                border: none;
            }
            QTableWidget::item:alternate {
                background: #f5f5f5;
            }
        """)
        layout.addWidget(self.table)

        # Tóm tắt
        self.summary_label = QLabel("Tổng: 0 cư dân")
        self.summary_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(self.summary_label)

    def refresh_data(self):
        """Làm mới dữ liệu."""
        # Cập nhật filter
        current_filter = self.room_filter.currentData()
        self.room_filter.blockSignals(True)
        self.room_filter.clear()
        self.room_filter.addItem("Tất cả phòng", None)
        rooms = db_manager.get_all_rooms()
        for room in rooms:
            self.room_filter.addItem(room["room_number"], room["id"])

        # Khôi phục filter
        if current_filter:
            for i in range(self.room_filter.count()):
                if self.room_filter.itemData(i) == current_filter:
                    self.room_filter.setCurrentIndex(i)
                    break
        self.room_filter.blockSignals(False)

        self._load_residents()

    def _apply_filter(self):
        """Áp dụng lọc phòng."""
        self._load_residents()

    def _load_residents(self):
        """Tải và hiển thị danh sách cư dân."""
        room_filter = self.room_filter.currentData()

        if room_filter:
            residents = db_manager.get_residents_by_room(room_filter, active_only=True)
        else:
            residents = db_manager.get_all_residents(active_only=True)

        self.table.setRowCount(0)
        for resident in residents:
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(str(resident["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(resident.get("room_number", "")))
            self.table.setItem(row, 2, QTableWidgetItem(resident.get("full_name", "")))
            self.table.setItem(row, 3, QTableWidgetItem(str(resident.get("age", "") or "")))
            self.table.setItem(row, 4, QTableWidgetItem(resident.get("id_card", "") or ""))
            self.table.setItem(row, 5, QTableWidgetItem(resident.get("phone", "") or ""))
            self.table.setItem(row, 6, QTableWidgetItem(format_date(resident.get("check_in_date", ""))))
            self.table.setItem(row, 7, QTableWidgetItem(resident.get("notes", "") or ""))

            # Action buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(3, 2, 3, 2)
            action_layout.setSpacing(4)

            edit_btn = QPushButton("✏️")
            edit_btn.setToolTip("Sửa thông tin")
            edit_btn.setFixedSize(30, 26)
            edit_btn.setStyleSheet("background: #1976D2; color: white; border-radius: 4px; font-size: 12px;")
            edit_btn.clicked.connect(lambda _, r=resident: self._edit_resident(r))
            action_layout.addWidget(edit_btn)

            checkout_btn = QPushButton("🚪")
            checkout_btn.setToolTip("Trả phòng")
            checkout_btn.setFixedSize(30, 26)
            checkout_btn.setStyleSheet("background: #F57C00; color: white; border-radius: 4px; font-size: 12px;")
            checkout_btn.clicked.connect(lambda _, r=resident: self._checkout_resident(r))
            action_layout.addWidget(checkout_btn)

            del_btn = QPushButton("🗑️")
            del_btn.setToolTip("Xóa")
            del_btn.setFixedSize(30, 26)
            del_btn.setStyleSheet("background: #D32F2F; color: white; border-radius: 4px; font-size: 12px;")
            del_btn.clicked.connect(lambda _, r=resident: self._delete_resident(r))
            action_layout.addWidget(del_btn)

            self.table.setCellWidget(row, 8, action_widget)
            self.table.setRowHeight(row, 40)

        self.summary_label.setText(f"Tổng: {len(residents)} cư dân đang ở")

    def _add_resident(self):
        """Mở dialog thêm cư dân."""
        rooms = db_manager.get_all_rooms()
        dialog = ResidentDialog(self, rooms=rooms)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                db_manager.add_resident(
                    data["room_id"], data["full_name"], data["age"],
                    data["id_card"], data["phone"], data["notes"],
                    data["check_in_date"]
                )
                self.refresh_data()
                QMessageBox.information(self, "Thành công", "Đã thêm cư dân thành công!")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể thêm cư dân: {e}")

    def _edit_resident(self, resident):
        """Mở dialog sửa thông tin cư dân."""
        rooms = db_manager.get_all_rooms()
        dialog = ResidentDialog(self, resident=resident, rooms=rooms)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                db_manager.update_resident(
                    resident["id"], data["full_name"], data["age"],
                    data["id_card"], data["phone"], data["notes"],
                    data["check_in_date"]
                )
                self.refresh_data()
                QMessageBox.information(self, "Thành công", "Đã cập nhật thông tin cư dân!")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể cập nhật: {e}")

    def _checkout_resident(self, resident):
        """Xử lý trả phòng."""
        reply = QMessageBox.question(
            self, "Xác nhận trả phòng",
            f"Cư dân '{resident['full_name']}' trả phòng ngày hôm nay?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                db_manager.checkout_resident(resident["id"])
                self.refresh_data()
                QMessageBox.information(self, "Thành công", "Đã ghi nhận trả phòng!")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể ghi nhận: {e}")

    def _delete_resident(self, resident):
        """Xóa cư dân."""
        reply = QMessageBox.warning(
            self, "Xác nhận xóa",
            f"Bạn có chắc muốn xóa cư dân '{resident['full_name']}'?\nThao tác này không thể hoàn tác!",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                db_manager.delete_resident(resident["id"])
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể xóa: {e}")
