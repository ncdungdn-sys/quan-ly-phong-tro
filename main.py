import sys
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTabWidget, QTableWidget, QTableWidgetItem,
                             QPushButton, QLabel, QLineEdit, QSpinBox, QDateEdit,
                             QDialog, QFormLayout, QMessageBox, QComboBox,
                             QDoubleSpinBox, QGroupBox, QTextEdit,
                             QHeaderView, QFrame, QSplitter)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont
from database import Database


class RoomManagementApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.selected_room_id = None       # Phòng đang chọn trong tab Phòng
        self.selected_log_room_id = None   # Phòng đang chọn trong tab Nhật Ký
        self.init_ui()
        self._check_billing_notifications()

    def init_ui(self):
        self.setWindowTitle("📁 Quản Lý Phòng Trọ")
        self.setGeometry(100, 100, 1200, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()

        # Tiêu đề
        title = QLabel("🏠 HỆ THỐNG QUẢN LÝ PHÒNG TRỌ")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)

        # Dashboard
        dashboard_layout = QHBoxLayout()
        self.total_rooms_label = QLabel("Tổng phòng: 0")
        self.empty_rooms_label = QLabel("Phòng trống: 0")
        self.total_residents_label = QLabel("Tổng cư dân: 0")
        dashboard_layout.addWidget(self.total_rooms_label)
        dashboard_layout.addWidget(self.empty_rooms_label)
        dashboard_layout.addWidget(self.total_residents_label)
        main_layout.addLayout(dashboard_layout)

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self.create_rooms_tab(), "🏘️ Phòng")
        tabs.addTab(self.create_residents_tab(), "👥 Cư Dân")
        tabs.addTab(self.create_bills_tab(), "📋 Hóa Đơn")
        tabs.addTab(self.create_electricity_tab(), "⚡ Điện")
        tabs.addTab(self.create_laundry_tab(), "👔 Giặt")
        tabs.addTab(self.create_expenses_tab(), "💰 Chi Phí")
        tabs.addTab(self.create_logs_tab(), "📔 Nhật Ký")
        tabs.addTab(self.create_reports_tab(), "📊 Báo Cáo")

        main_layout.addWidget(tabs)
        central_widget.setLayout(main_layout)

        self.update_dashboard()

    # ===== BILLING NOTIFICATION =====
    def _check_billing_notifications(self):
        """Kiểm tra và hiện thông báo thu tiền (mỗi phòng chỉ 1 lần/ngày)"""
        today = datetime.now().strftime('%Y-%m-%d')
        today_day = datetime.now().day
        self.db.clear_old_reminders()

        rooms = self.db.get_all_rooms()
        for room in rooms:
            if room['status'] == 'occupied' and room['billing_day'] == today_day:
                if not self.db.check_reminder_exists(room['id'], today):
                    msg = QMessageBox(self)
                    msg.setWindowTitle("🔔 Nhắc Nhở Thu Tiền")
                    msg.setText(
                        f"Hôm nay là ngày tính tiền phòng {room['name']}!\n\n"
                        "Vui lòng thu tiền phòng!"
                    )
                    msg.setIcon(QMessageBox.Information)
                    msg.addButton("👍 Đã Xem", QMessageBox.AcceptRole)
                    msg.exec_()
                    self.db.create_reminder_log(room['id'], today)

    # ===== TAB PHÒNG =====
    def create_rooms_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        # Nút thao tác
        btn_layout = QHBoxLayout()
        add_room_btn = QPushButton("➕ Thêm Phòng")
        add_room_btn.clicked.connect(self.add_room_dialog)
        self.add_resident_btn = QPushButton("➕ Thêm Khách")
        self.add_resident_btn.clicked.connect(self.add_resident_to_selected_room)
        self.delete_room_btn = QPushButton("🗑️ Xóa Phòng")
        self.delete_room_btn.clicked.connect(self.delete_selected_room)
        btn_layout.addWidget(add_room_btn)
        btn_layout.addWidget(self.add_resident_btn)
        btn_layout.addWidget(self.delete_room_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Bảng phòng
        self.rooms_table = QTableWidget()
        self.rooms_table.setColumnCount(5)
        self.rooms_table.setHorizontalHeaderLabels(["ID", "Phòng", "Giá", "Trạng Thái", "Ngày Tính Tiền"])
        self.rooms_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.rooms_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.rooms_table.itemSelectionChanged.connect(self._on_room_selection_changed)
        self.rooms_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.rooms_table)

        widget.setLayout(layout)
        return widget

    def _on_room_selection_changed(self):
        """Cập nhật selected_room_id khi chọn dòng trong bảng phòng"""
        selected_rows = self.rooms_table.selectedItems()
        if selected_rows:
            row = self.rooms_table.currentRow()
            id_item = self.rooms_table.item(row, 0)
            if id_item:
                self.selected_room_id = int(id_item.text())
        else:
            self.selected_room_id = None

    def add_resident_to_selected_room(self):
        """Thêm khách vào phòng đang chọn"""
        if not self.selected_room_id:
            QMessageBox.warning(self, "Chưa Chọn Phòng", "Vui lòng chọn phòng trước!")
            return
        room = self.db.get_room_by_id(self.selected_room_id)
        if not room:
            QMessageBox.warning(self, "Lỗi", "Phòng không tồn tại!")
            return
        self._open_add_resident_dialog(preselected_room_id=self.selected_room_id,
                                       preselected_room_name=room['name'])

    def delete_selected_room(self):
        """Xóa phòng đang chọn (cascade xóa khách và dữ liệu liên quan)"""
        if not self.selected_room_id:
            QMessageBox.warning(self, "Chưa Chọn Phòng", "Vui lòng chọn phòng trước!")
            return
        room = self.db.get_room_by_id(self.selected_room_id)
        if not room:
            return
        reply = QMessageBox.question(
            self, "Xác Nhận Xóa",
            f"Bạn có chắc muốn xóa phòng '{room['name']}'?\n"
            "⚠️ Tất cả dữ liệu liên quan (khách, nhật ký, hóa đơn...) sẽ bị xóa!",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.delete_room(self.selected_room_id)
            self.selected_room_id = None
            self.update_dashboard()

    def refresh_rooms_table(self):
        """Load danh sách phòng vào bảng"""
        rooms = self.db.get_all_rooms()
        self.rooms_table.setRowCount(len(rooms))
        for row_idx, room in enumerate(rooms):
            self.rooms_table.setItem(row_idx, 0, QTableWidgetItem(str(room['id'])))
            self.rooms_table.setItem(row_idx, 1, QTableWidgetItem(room['name']))
            self.rooms_table.setItem(row_idx, 2, QTableWidgetItem(f"{room['price']:,.0f}đ"))
            status_text = "Có Khách" if room['status'] == 'occupied' else "Trống"
            self.rooms_table.setItem(row_idx, 3, QTableWidgetItem(status_text))
            billing_day = room['billing_day'] or 1
            self.rooms_table.setItem(row_idx, 4, QTableWidgetItem(f"Ngày {billing_day}"))

    # ===== TAB CƯ DÂN =====
    def create_residents_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        btn_layout = QHBoxLayout()
        add_button = QPushButton("➕ Thêm Cư Dân")
        add_button.clicked.connect(self.add_resident_dialog)
        self.edit_resident_btn = QPushButton("✏️ Sửa")
        self.edit_resident_btn.clicked.connect(self.edit_resident_dialog)
        self.delete_resident_btn = QPushButton("🗑️ Xóa")
        self.delete_resident_btn.clicked.connect(self.delete_selected_resident)
        btn_layout.addWidget(add_button)
        btn_layout.addWidget(self.edit_resident_btn)
        btn_layout.addWidget(self.delete_resident_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.residents_table = QTableWidget()
        self.residents_table.setColumnCount(7)
        self.residents_table.setHorizontalHeaderLabels(
            ["ID", "Tên", "Tuổi", "CCCD", "SĐT", "Phòng", "Ngày Vào"])
        self.residents_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.residents_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.residents_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.residents_table)

        widget.setLayout(layout)
        return widget

    def refresh_residents_table(self):
        """Load danh sách cư dân vào bảng"""
        residents = self.db.get_all_residents()
        self.residents_table.setRowCount(len(residents))
        for row_idx, r in enumerate(residents):
            self.residents_table.setItem(row_idx, 0, QTableWidgetItem(str(r['id'])))
            self.residents_table.setItem(row_idx, 1, QTableWidgetItem(r['name'] or ''))
            self.residents_table.setItem(row_idx, 2, QTableWidgetItem(str(r['age'] or '')))
            self.residents_table.setItem(row_idx, 3, QTableWidgetItem(r['cccd'] or ''))
            self.residents_table.setItem(row_idx, 4, QTableWidgetItem(r['phone'] or ''))
            self.residents_table.setItem(row_idx, 5, QTableWidgetItem(r['room_name'] or ''))
            self.residents_table.setItem(row_idx, 6, QTableWidgetItem(str(r['check_in_date'] or '')))

    def add_resident_dialog(self):
        self._open_add_resident_dialog()

    def _open_add_resident_dialog(self, preselected_room_id=None, preselected_room_name=None):
        dialog = QDialog(self)
        dialog.setWindowTitle("Thêm Cư Dân")
        dialog.setGeometry(200, 200, 400, 320)

        form_layout = QFormLayout()

        name_input = QLineEdit()
        age_input = QSpinBox()
        age_input.setRange(1, 120)
        cccd_input = QLineEdit()
        phone_input = QLineEdit()
        room_combo = QComboBox()
        date_input = QDateEdit()
        date_input.setDate(QDate.currentDate())
        date_input.setCalendarPopup(True)

        if preselected_room_id:
            room_combo.addItem(preselected_room_name, preselected_room_id)
            room_combo.setEnabled(False)
        else:
            rooms = self.db.get_all_rooms()
            for room in rooms:
                room_combo.addItem(room['name'], room['id'])

        form_layout.addRow("Tên:", name_input)
        form_layout.addRow("Tuổi:", age_input)
        form_layout.addRow("CCCD:", cccd_input)
        form_layout.addRow("SĐT:", phone_input)
        form_layout.addRow("Phòng:", room_combo)
        form_layout.addRow("Ngày Vào:", date_input)

        save_button = QPushButton("💾 Lưu")
        save_button.clicked.connect(lambda: self._save_resident(
            dialog, name_input.text(), age_input.value(), cccd_input.text(),
            phone_input.text(), room_combo.currentData(), date_input.date()
        ))
        form_layout.addRow(save_button)

        dialog.setLayout(form_layout)
        dialog.exec_()

    def _save_resident(self, dialog, name, age, cccd, phone, room_id, date):
        if not name.strip():
            QMessageBox.warning(dialog, "Lỗi", "Vui lòng nhập tên cư dân!")
            return
        if not room_id:
            QMessageBox.warning(dialog, "Lỗi", "Vui lòng chọn phòng!")
            return
        try:
            self.db.add_resident(name.strip(), age, cccd.strip(), phone.strip(),
                                 room_id, date.toString("yyyy-MM-dd"))
            QMessageBox.information(dialog, "Thành công", "Cư dân đã được thêm!")
            dialog.accept()
            self.update_dashboard()
        except Exception as e:
            QMessageBox.critical(dialog, "Lỗi", str(e))

    def edit_resident_dialog(self):
        selected = self.residents_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Chưa Chọn", "Vui lòng chọn cư dân cần sửa!")
            return
        row = self.residents_table.currentRow()
        resident_id = int(self.residents_table.item(row, 0).text())
        resident = self.db.get_resident_by_id(resident_id)
        if not resident:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Sửa Cư Dân")
        dialog.setGeometry(200, 200, 400, 280)

        form_layout = QFormLayout()
        name_input = QLineEdit(resident['name'] or '')
        age_input = QSpinBox()
        age_input.setRange(1, 120)
        age_input.setValue(resident['age'] or 1)
        phone_input = QLineEdit(resident['phone'] or '')
        notes_input = QLineEdit(resident['notes'] or '')

        form_layout.addRow("Tên:", name_input)
        form_layout.addRow("Tuổi:", age_input)
        form_layout.addRow("SĐT:", phone_input)
        form_layout.addRow("Ghi Chú:", notes_input)

        save_button = QPushButton("💾 Lưu")
        save_button.clicked.connect(lambda: self._save_edit_resident(
            dialog, resident_id, name_input.text(), age_input.value(),
            phone_input.text(), notes_input.text()
        ))
        form_layout.addRow(save_button)
        dialog.setLayout(form_layout)
        dialog.exec_()

    def _save_edit_resident(self, dialog, resident_id, name, age, phone, notes):
        if not name.strip():
            QMessageBox.warning(dialog, "Lỗi", "Vui lòng nhập tên cư dân!")
            return
        try:
            self.db.update_resident(resident_id, name.strip(), age, phone.strip(), notes.strip())
            QMessageBox.information(dialog, "Thành công", "Đã cập nhật thông tin cư dân!")
            dialog.accept()
            self.refresh_residents_table()
        except Exception as e:
            QMessageBox.critical(dialog, "Lỗi", str(e))

    def delete_selected_resident(self):
        selected = self.residents_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Chưa Chọn", "Vui lòng chọn cư dân cần xóa!")
            return
        row = self.residents_table.currentRow()
        resident_id = int(self.residents_table.item(row, 0).text())
        name = self.residents_table.item(row, 1).text()
        reply = QMessageBox.question(
            self, "Xác Nhận Xóa",
            f"Bạn có chắc muốn xóa cư dân '{name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.delete_resident(resident_id)
            self.update_dashboard()

    # ===== TAB HÓA ĐƠN =====
    def create_bills_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        # Selector: Phòng + Tháng
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Phòng:"))
        self.bill_room_combo = QComboBox()
        self.bill_room_combo.currentIndexChanged.connect(self.on_bill_selector_changed)
        selector_layout.addWidget(self.bill_room_combo)

        selector_layout.addWidget(QLabel("Tháng:"))
        self.bill_month = QDateEdit()
        self.bill_month.setDate(QDate.currentDate())
        self.bill_month.setCalendarPopup(True)
        self.bill_month.dateChanged.connect(self.on_bill_selector_changed)
        selector_layout.addWidget(self.bill_month)
        selector_layout.addStretch()
        layout.addLayout(selector_layout)

        # Nội dung: Trái (nhập liệu) | Phải (xem trước + thanh toán)
        content_layout = QHBoxLayout()

        # --- Trái: Form nhập liệu ---
        left_widget = QWidget()
        left_layout = QVBoxLayout()

        # Electricity
        elec_group = QGroupBox("⚡ Tiền Điện")
        elec_form = QFormLayout()
        self.bill_elec_old = QDoubleSpinBox()
        self.bill_elec_old.setMaximum(999999)
        self.bill_elec_old.setDecimals(0)
        self.bill_elec_new = QDoubleSpinBox()
        self.bill_elec_new.setMaximum(999999)
        self.bill_elec_new.setDecimals(0)
        self.bill_elec_result = QLabel("→ 0 số × 3.500đ = 0đ")
        self.bill_elec_old.valueChanged.connect(self.update_bill_preview)
        self.bill_elec_new.valueChanged.connect(self.update_bill_preview)
        elec_form.addRow("Chỉ số cũ:", self.bill_elec_old)
        elec_form.addRow("Chỉ số mới:", self.bill_elec_new)
        elec_form.addRow(self.bill_elec_result)
        elec_group.setLayout(elec_form)
        left_layout.addWidget(elec_group)

        # Water (auto-calc)
        water_group = QGroupBox("💧 Tiền Nước (tự động)")
        water_form = QFormLayout()
        self.bill_water_info = QLabel("→ 0 người × 50.000đ = 0đ")
        water_form.addRow(self.bill_water_info)
        water_group.setLayout(water_form)
        left_layout.addWidget(water_group)

        # Laundry (auto-calc)
        laundry_group = QGroupBox("👔 Tiền Giặt (tự động)")
        laundry_form = QFormLayout()
        self.bill_laundry_info = QLabel("→ 0 người × 20.000đ = 0đ")
        laundry_form.addRow(self.bill_laundry_info)
        laundry_group.setLayout(laundry_form)
        left_layout.addWidget(laundry_group)

        # Internet + Trash
        inet_group = QGroupBox("💰 Chi Phí (Internet + Rác)")
        inet_form = QFormLayout()
        self.bill_inet_amount = QDoubleSpinBox()
        self.bill_inet_amount.setMaximum(9999999)
        self.bill_inet_amount.setDecimals(0)
        self.bill_inet_amount.valueChanged.connect(self.update_bill_preview)
        self.bill_inet_notes = QLineEdit()
        self.bill_inet_notes.setPlaceholderText("VD: Internet 100k + Rác 30k")
        inet_form.addRow("Số tiền:", self.bill_inet_amount)
        inet_form.addRow("Ghi chú:", self.bill_inet_notes)
        inet_group.setLayout(inet_form)
        left_layout.addWidget(inet_group)

        left_layout.addStretch()
        left_widget.setLayout(left_layout)
        content_layout.addWidget(left_widget, 1)

        # --- Phải: Xem trước + Thanh toán ---
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("📄 Xem Trước Hóa Đơn:"))
        self.bill_preview = QTextEdit()
        self.bill_preview.setReadOnly(True)
        mono_font = QFont("Courier New", 10)
        self.bill_preview.setFont(mono_font)
        right_layout.addWidget(self.bill_preview)

        pay_button = QPushButton("✅ Thanh Toán")
        pay_button.setStyleSheet(
            "QPushButton { background-color: #28a745; color: white; font-size: 14px; "
            "font-weight: bold; padding: 10px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #218838; }"
        )
        pay_button.clicked.connect(self.process_payment)
        right_layout.addWidget(pay_button)

        right_widget.setLayout(right_layout)
        content_layout.addWidget(right_widget, 1)

        layout.addLayout(content_layout)
        widget.setLayout(layout)
        return widget

    def on_bill_selector_changed(self):
        """Cập nhật xem trước khi đổi phòng/tháng"""
        self.update_bill_preview()

    def load_bill_combos(self):
        """Load danh sách phòng vào combo hóa đơn và điện"""
        rooms = self.db.get_all_rooms()

        self.bill_room_combo.blockSignals(True)
        current_data = self.bill_room_combo.currentData()
        self.bill_room_combo.clear()
        for room in rooms:
            self.bill_room_combo.addItem(room['name'], room['id'])
        if current_data:
            for i in range(self.bill_room_combo.count()):
                if self.bill_room_combo.itemData(i) == current_data:
                    self.bill_room_combo.setCurrentIndex(i)
                    break
        self.bill_room_combo.blockSignals(False)

        self._refresh_elec_room_combo()
        self.update_bill_preview()

    def update_bill_preview(self):
        """Cập nhật xem trước hóa đơn"""
        room_id = self.bill_room_combo.currentData()
        if not room_id:
            self.bill_preview.clear()
            return

        room_name = self.bill_room_combo.currentText()
        room_price = self.db.get_room_price(room_id)
        month_qdate = self.bill_month.date()
        month_display = f"{month_qdate.month():02d}/{month_qdate.year()}"

        num_residents = self.db.get_residents_count_by_room(room_id)

        # Electricity
        old_reading = self.bill_elec_old.value()
        new_reading = self.bill_elec_new.value()
        kwh = max(0, new_reading - old_reading)
        elec_price = self.db.get_setting('electricity_price') or 3500
        electricity_fee = kwh * elec_price
        self.bill_elec_result.setText(
            f"→ {kwh:.0f} số × {elec_price:,.0f}đ = {electricity_fee:,.0f}đ"
        )

        # Water (per person × 50,000)
        water_fee = num_residents * 50000
        self.bill_water_info.setText(
            f"→ {num_residents} người × 50.000đ = {water_fee:,.0f}đ"
        )

        # Laundry (per person × 20,000)
        laundry_fee = num_residents * 20000
        self.bill_laundry_info.setText(
            f"→ {num_residents} người × 20.000đ = {laundry_fee:,.0f}đ"
        )

        # Internet + Trash
        inet_amount = self.bill_inet_amount.value()
        inet_notes = self.bill_inet_notes.text() or '-'

        total = room_price + electricity_fee + water_fee + laundry_fee + inet_amount

        sep = "━" * 26
        preview = (
            f"{sep}\n"
            f"    HÓA ĐƠN TIỀN PHÒNG\n"
            f"{sep}\n"
            f"\n"
            f"Phòng:   {room_name}\n"
            f"Tháng:   {month_display}\n"
            f"Số Người:{num_residents}\n"
            f"\n"
            f"━━━ CHI TIẾT ━━━\n"
            f"Tiền Phòng:  {room_price:>12,.0f}đ\n"
            f"Tiền Nước:   {water_fee:>12,.0f}đ ({num_residents} người × 50.000đ)\n"
            f"Tiền Giặt:   {laundry_fee:>12,.0f}đ ({num_residents} người × 20.000đ)\n"
            f"Chi Phí:     {inet_amount:>12,.0f}đ ({inet_notes})\n"
            f"Tiền Điện:   {electricity_fee:>12,.0f}đ ({kwh:.0f} số × {elec_price:,.0f}đ)\n"
            f"\n"
            f"━━━ TỔNG ━━━\n"
            f"TỔNG HÓA ĐƠN:{total:>12,.0f}đ\n"
            f"\n"
            f"{sep}"
        )
        self.bill_preview.setText(preview)

    def process_payment(self):
        """Xử lý thanh toán và lưu hóa đơn"""
        room_id = self.bill_room_combo.currentData()
        if not room_id:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn phòng!")
            return

        room_name = self.bill_room_combo.currentText()
        month_qdate = self.bill_month.date()
        month_str = month_qdate.toString("yyyy-MM-01")
        month_display = f"{month_qdate.month()}/{month_qdate.year()}"

        room_price = self.db.get_room_price(room_id)
        num_residents = self.db.get_residents_count_by_room(room_id)
        old_reading = self.bill_elec_old.value()
        new_reading = self.bill_elec_new.value()
        kwh = max(0, new_reading - old_reading)
        elec_price = self.db.get_setting('electricity_price') or 3500
        electricity_fee = kwh * elec_price
        water_fee = num_residents * 50000
        laundry_fee = num_residents * 20000
        inet_amount = self.bill_inet_amount.value()
        inet_notes = self.bill_inet_notes.text()

        try:
            self.db.save_monthly_bill(
                room_id=room_id,
                month=month_str,
                room_fee=room_price,
                electricity_fee=electricity_fee,
                water_fee=water_fee,
                laundry_fee=laundry_fee,
                internet_trash_fee=inet_amount,
                internet_trash_notes=inet_notes,
                elec_old_reading=old_reading,
                elec_new_reading=new_reading,
                num_residents=num_residents,
            )
            QMessageBox.information(
                self, "✅ Thanh Toán Thành Công",
                f"Đã thanh toán tháng {month_display}\nPhòng: {room_name}"
            )
            # Reset các trường nhập liệu
            self.bill_elec_old.setValue(0)
            self.bill_elec_new.setValue(0)
            self.bill_inet_amount.setValue(0)
            self.bill_inet_notes.clear()
            self.update_bill_preview()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e))

    # ===== TAB ĐIỆN =====
    def create_electricity_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        form_layout = QFormLayout()
        self.elec_room_combo = QComboBox()
        self.elec_month = QDateEdit()
        self.elec_month.setDate(QDate.currentDate())
        self.elec_reading = QDoubleSpinBox()
        self.elec_reading.setMaximum(999999)

        form_layout.addRow("Phòng:", self.elec_room_combo)
        form_layout.addRow("Tháng:", self.elec_month)
        form_layout.addRow("Mốc Điện:", self.elec_reading)

        layout.addLayout(form_layout)

        save_button = QPushButton("💾 Lưu Mốc Điện")
        save_button.clicked.connect(self.save_electricity)
        layout.addWidget(save_button)

        self.electricity_table = QTableWidget()
        self.electricity_table.setColumnCount(4)
        self.electricity_table.setHorizontalHeaderLabels(["Phòng", "Tháng", "Mốc", "Tiền Điện"])
        self.electricity_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.electricity_table)

        widget.setLayout(layout)
        return widget

    def _refresh_elec_room_combo(self):
        self.elec_room_combo.clear()
        rooms = self.db.get_all_rooms()
        for room in rooms:
            self.elec_room_combo.addItem(room['name'], room['id'])

    def save_electricity(self):
        room_id = self.elec_room_combo.currentData()
        if not room_id:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn phòng!")
            return
        month = self.elec_month.date().toString("yyyy-MM-dd")
        reading = self.elec_reading.value()
        try:
            self.db.add_electricity_reading(room_id, month, reading)
            QMessageBox.information(self, "Lưu", "Mốc điện đã được lưu!")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e))

    # ===== TAB GIẶT =====
    def create_laundry_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("📋 Quản Lý Giặt Quần Áo"))

        self.laundry_table = QTableWidget()
        self.laundry_table.setColumnCount(4)
        self.laundry_table.setHorizontalHeaderLabels(["Phòng", "Số Người", "Tiền Giặt", "Tháng"])
        self.laundry_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.laundry_table)

        widget.setLayout(layout)
        return widget

    # ===== TAB CHI PHÍ =====
    def create_expenses_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        btn_layout = QHBoxLayout()
        add_button = QPushButton("➕ Thêm Chi Phí")
        add_button.clicked.connect(self.add_expense_dialog)
        btn_layout.addWidget(add_button)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.expenses_table = QTableWidget()
        self.expenses_table.setColumnCount(5)
        self.expenses_table.setHorizontalHeaderLabels(["Loại", "Mô Tả", "Số Tiền", "Phòng", "Ngày"])
        self.expenses_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.expenses_table)

        widget.setLayout(layout)
        return widget

    def add_expense_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Thêm Chi Phí")
        dialog.setGeometry(200, 200, 400, 250)

        form_layout = QFormLayout()

        expense_type = QComboBox()
        expense_type.addItems(["Sửa Chữa Chung", "Bảo Trì", "Internet", "Rác", "Chi Phí Phòng"])
        expense_desc = QLineEdit()
        expense_amount = QDoubleSpinBox()
        expense_amount.setMaximum(99999999)
        expense_amount.setDecimals(0)

        form_layout.addRow("Loại Chi Phí:", expense_type)
        form_layout.addRow("Mô Tả:", expense_desc)
        form_layout.addRow("Số Tiền (đ):", expense_amount)

        save_button = QPushButton("💾 Lưu")
        save_button.clicked.connect(lambda: self._save_expense(
            dialog, expense_type.currentText(), expense_desc.text(), expense_amount.value()
        ))
        form_layout.addRow(save_button)

        dialog.setLayout(form_layout)
        dialog.exec_()

    def _save_expense(self, dialog, exp_type, description, amount):
        try:
            self.db.add_expense(exp_type, description, amount)
            QMessageBox.information(dialog, "Thành công", "Chi phí đã được thêm!")
            dialog.accept()
            self._refresh_expenses_table()
        except Exception as e:
            QMessageBox.critical(dialog, "Lỗi", str(e))

    def _refresh_expenses_table(self):
        expenses = self.db.get_all_expenses()
        self.expenses_table.setRowCount(len(expenses))
        for row_idx, exp in enumerate(expenses):
            self.expenses_table.setItem(row_idx, 0, QTableWidgetItem(exp['type'] or ''))
            self.expenses_table.setItem(row_idx, 1, QTableWidgetItem(exp['description'] or ''))
            self.expenses_table.setItem(row_idx, 2, QTableWidgetItem(f"{exp['amount']:,.0f}đ"))
            self.expenses_table.setItem(row_idx, 3, QTableWidgetItem(str(exp['room_id'] or '')))
            self.expenses_table.setItem(row_idx, 4, QTableWidgetItem(str(exp['date'] or '')))

    # ===== TAB NHẬT KÝ =====
    def create_logs_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        # --- Filter Bar ---
        filter_frame = QFrame()
        filter_frame.setFrameShape(QFrame.StyledPanel)
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Loại:"))
        self.log_filter_category = QComboBox()
        self.log_filter_category.addItems(["Tất Cả", "Hư Hỏng", "Sửa Chữa", "Phản Ánh", "Ghi Chú"])
        filter_layout.addWidget(self.log_filter_category)

        filter_layout.addWidget(QLabel("Trạng Thái:"))
        self.log_filter_status = QComboBox()
        self.log_filter_status.addItems(["Tất Cả", "Chưa Xử Lý", "Đang Xử Lý", "Xong"])
        filter_layout.addWidget(self.log_filter_status)

        filter_layout.addWidget(QLabel("Từ:"))
        self.log_filter_from = QDateEdit()
        self.log_filter_from.setDate(QDate.currentDate().addMonths(-1))
        self.log_filter_from.setCalendarPopup(True)
        filter_layout.addWidget(self.log_filter_from)

        filter_layout.addWidget(QLabel("Đến:"))
        self.log_filter_to = QDateEdit()
        self.log_filter_to.setDate(QDate.currentDate())
        self.log_filter_to.setCalendarPopup(True)
        filter_layout.addWidget(self.log_filter_to)

        filter_btn = QPushButton("🔍 Lọc")
        filter_btn.clicked.connect(self._apply_log_filter)
        filter_layout.addWidget(filter_btn)

        filter_frame.setLayout(filter_layout)
        layout.addWidget(filter_frame)

        # --- Nội dung: Trái (danh sách phòng) + Phải (chi tiết nhật ký) ---
        splitter = QSplitter(Qt.Horizontal)

        # Trái: Danh sách phòng
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("📋 Danh Sách Phòng"))
        self.log_rooms_table = QTableWidget()
        self.log_rooms_table.setColumnCount(2)
        self.log_rooms_table.setHorizontalHeaderLabels(["Phòng", "Trạng Thái"])
        self.log_rooms_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.log_rooms_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.log_rooms_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.log_rooms_table.itemSelectionChanged.connect(self._on_log_room_selection_changed)
        left_layout.addWidget(self.log_rooms_table)
        left_widget.setLayout(left_layout)

        # Phải: Chi tiết nhật ký
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        self.log_room_title = QLabel("📔 Nhật Ký Phòng")
        title_font = QFont()
        title_font.setBold(True)
        self.log_room_title.setFont(title_font)
        right_layout.addWidget(self.log_room_title)

        log_btn_layout = QHBoxLayout()
        add_log_btn = QPushButton("➕ Thêm")
        add_log_btn.clicked.connect(self.add_log_dialog)
        self.edit_log_btn = QPushButton("✏️ Sửa")
        self.edit_log_btn.clicked.connect(self.edit_log_dialog)
        self.delete_log_btn = QPushButton("🗑️ Xóa")
        self.delete_log_btn.clicked.connect(self.delete_selected_log)
        log_btn_layout.addWidget(add_log_btn)
        log_btn_layout.addWidget(self.edit_log_btn)
        log_btn_layout.addWidget(self.delete_log_btn)
        log_btn_layout.addStretch()
        right_layout.addLayout(log_btn_layout)

        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(5)
        self.logs_table.setHorizontalHeaderLabels(["ID", "Ngày", "Loại", "Ghi Chú", "Trạng Thái"])
        self.logs_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.logs_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.logs_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_layout.addWidget(self.logs_table)
        right_widget.setLayout(right_layout)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 700])
        layout.addWidget(splitter)

        widget.setLayout(layout)
        return widget

    def _refresh_log_rooms_table(self):
        rooms = self.db.get_all_rooms()
        self.log_rooms_table.setRowCount(len(rooms))
        for row_idx, room in enumerate(rooms):
            self.log_rooms_table.setItem(row_idx, 0, QTableWidgetItem(room['name']))
            status_text = "Có Khách" if room['status'] == 'occupied' else "Trống"
            self.log_rooms_table.setItem(row_idx, 1, QTableWidgetItem(status_text))
            self.log_rooms_table.item(row_idx, 0).setData(Qt.UserRole, room['id'])

    def _on_log_room_selection_changed(self):
        selected = self.log_rooms_table.selectedItems()
        if selected:
            row = self.log_rooms_table.currentRow()
            item = self.log_rooms_table.item(row, 0)
            if item:
                self.selected_log_room_id = item.data(Qt.UserRole)
                room_name = item.text()
                self.log_room_title.setText(f"📔 Nhật Ký Phòng {room_name}")
                self._refresh_logs_table()
        else:
            self.selected_log_room_id = None

    def _apply_log_filter(self):
        self._refresh_logs_table()

    def _refresh_logs_table(self):
        if not self.selected_log_room_id:
            self.logs_table.setRowCount(0)
            return
        category = self.log_filter_category.currentText()
        status = self.log_filter_status.currentText()
        date_from = self.log_filter_from.date().toString("yyyy-MM-dd")
        date_to = self.log_filter_to.date().toString("yyyy-MM-dd")
        logs = self.db.get_room_logs(
            self.selected_log_room_id,
            category=category if category != 'Tất Cả' else None,
            status=status if status != 'Tất Cả' else None,
            date_from=date_from,
            date_to=date_to
        )
        self.logs_table.setRowCount(len(logs))
        for row_idx, log in enumerate(logs):
            self.logs_table.setItem(row_idx, 0, QTableWidgetItem(str(log['id'])))
            self.logs_table.setItem(row_idx, 1, QTableWidgetItem(log['date'] or ''))
            self.logs_table.setItem(row_idx, 2, QTableWidgetItem(log['category'] or ''))
            self.logs_table.setItem(row_idx, 3, QTableWidgetItem(log['note'] or ''))
            self.logs_table.setItem(row_idx, 4, QTableWidgetItem(log['status'] or ''))

    def add_log_dialog(self):
        if not self.selected_log_room_id:
            QMessageBox.warning(self, "Chưa Chọn Phòng", "Vui lòng chọn phòng trong danh sách!")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Thêm Nhật Ký")
        dialog.setGeometry(200, 200, 400, 280)
        form_layout = QFormLayout()

        date_input = QDateEdit()
        date_input.setDate(QDate.currentDate())
        date_input.setCalendarPopup(True)
        category_combo = QComboBox()
        category_combo.addItems(["Hư Hỏng", "Sửa Chữa", "Phản Ánh", "Ghi Chú"])
        note_input = QTextEdit()
        note_input.setMaximumHeight(80)
        status_combo = QComboBox()
        status_combo.addItems(["Chưa Xử Lý", "Đang Xử Lý", "Xong"])

        form_layout.addRow("Ngày:", date_input)
        form_layout.addRow("Loại:", category_combo)
        form_layout.addRow("Ghi Chú:", note_input)
        form_layout.addRow("Trạng Thái:", status_combo)

        save_btn = QPushButton("💾 Lưu")
        save_btn.clicked.connect(lambda: self._save_log(
            dialog,
            date_input.date().toString("yyyy-MM-dd"),
            category_combo.currentText(),
            note_input.toPlainText(),
            status_combo.currentText()
        ))
        form_layout.addRow(save_btn)
        dialog.setLayout(form_layout)
        dialog.exec_()

    def _save_log(self, dialog, date, category, note, status):
        try:
            self.db.add_room_log(self.selected_log_room_id, date, category, note, status)
            QMessageBox.information(dialog, "Thành công", "Đã thêm nhật ký!")
            dialog.accept()
            self._refresh_logs_table()
        except Exception as e:
            QMessageBox.critical(dialog, "Lỗi", str(e))

    def edit_log_dialog(self):
        selected = self.logs_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Chưa Chọn", "Vui lòng chọn nhật ký cần sửa!")
            return
        row = self.logs_table.currentRow()
        log_id = int(self.logs_table.item(row, 0).text())
        current_date = self.logs_table.item(row, 1).text()
        current_cat = self.logs_table.item(row, 2).text()
        current_note = self.logs_table.item(row, 3).text()
        current_status = self.logs_table.item(row, 4).text()

        dialog = QDialog(self)
        dialog.setWindowTitle("Sửa Nhật Ký")
        dialog.setGeometry(200, 200, 400, 280)
        form_layout = QFormLayout()

        date_input = QDateEdit()
        date_input.setDate(
            QDate.fromString(current_date, "yyyy-MM-dd") if current_date else QDate.currentDate()
        )
        date_input.setCalendarPopup(True)
        category_combo = QComboBox()
        category_combo.addItems(["Hư Hỏng", "Sửa Chữa", "Phản Ánh", "Ghi Chú"])
        idx = category_combo.findText(current_cat)
        if idx >= 0:
            category_combo.setCurrentIndex(idx)
        note_input = QTextEdit()
        note_input.setMaximumHeight(80)
        note_input.setPlainText(current_note)
        status_combo = QComboBox()
        status_combo.addItems(["Chưa Xử Lý", "Đang Xử Lý", "Xong"])
        idx2 = status_combo.findText(current_status)
        if idx2 >= 0:
            status_combo.setCurrentIndex(idx2)

        form_layout.addRow("Ngày:", date_input)
        form_layout.addRow("Loại:", category_combo)
        form_layout.addRow("Ghi Chú:", note_input)
        form_layout.addRow("Trạng Thái:", status_combo)

        save_btn = QPushButton("💾 Lưu")
        save_btn.clicked.connect(lambda: self._update_log(
            dialog, log_id,
            date_input.date().toString("yyyy-MM-dd"),
            category_combo.currentText(),
            note_input.toPlainText(),
            status_combo.currentText()
        ))
        form_layout.addRow(save_btn)
        dialog.setLayout(form_layout)
        dialog.exec_()

    def _update_log(self, dialog, log_id, date, category, note, status):
        try:
            self.db.update_room_log(log_id, date, category, note, status)
            QMessageBox.information(dialog, "Thành công", "Đã cập nhật nhật ký!")
            dialog.accept()
            self._refresh_logs_table()
        except Exception as e:
            QMessageBox.critical(dialog, "Lỗi", str(e))

    def delete_selected_log(self):
        selected = self.logs_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Chưa Chọn", "Vui lòng chọn nhật ký cần xóa!")
            return
        row = self.logs_table.currentRow()
        log_id = int(self.logs_table.item(row, 0).text())
        reply = QMessageBox.question(
            self, "Xác Nhận Xóa", "Bạn có chắc muốn xóa nhật ký này?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.delete_room_log(log_id)
            self._refresh_logs_table()

    # ===== TAB BÁO CÁO =====
    def create_reports_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        export_button = QPushButton("📊 Xuất Báo Cáo Excel")
        export_button.clicked.connect(self.export_report)
        layout.addWidget(export_button)

        self.reports_table = QTableWidget()
        self.reports_table.setColumnCount(5)
        self.reports_table.setHorizontalHeaderLabels(
            ["Tháng", "Doanh Thu", "Chi Phí", "Lợi Nhuận", "% Lợi Nhuận"])
        self.reports_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.reports_table)

        widget.setLayout(layout)
        return widget

    def export_report(self):
        QMessageBox.information(self, "Xuất", "Báo cáo đang được xuất...")

    # ===== DIALOG THÊM PHÒNG =====
    def add_room_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Thêm Phòng")
        dialog.setGeometry(200, 200, 320, 220)

        form_layout = QFormLayout()
        room_name = QLineEdit()
        room_price = QDoubleSpinBox()
        room_price.setMaximum(99999999)
        room_price.setDecimals(0)
        billing_day_input = QSpinBox()
        billing_day_input.setRange(1, 28)
        billing_day_input.setValue(1)

        form_layout.addRow("Tên Phòng:", room_name)
        form_layout.addRow("Giá Phòng (đ):", room_price)
        form_layout.addRow("Ngày Tính Tiền:", billing_day_input)

        save_button = QPushButton("💾 Lưu")
        save_button.clicked.connect(lambda: self._save_room(
            dialog, room_name.text(), room_price.value(), billing_day_input.value()
        ))
        form_layout.addRow(save_button)
        dialog.setLayout(form_layout)
        dialog.exec_()

    def _save_room(self, dialog, name, price, billing_day):
        if not name.strip():
            QMessageBox.warning(dialog, "Lỗi", "Vui lòng nhập tên phòng!")
            return
        try:
            self.db.add_room(name.strip(), price, billing_day)
            QMessageBox.information(dialog, "Thành công", "Phòng đã được thêm!")
            dialog.accept()
            self.update_dashboard()
        except Exception as e:
            QMessageBox.critical(dialog, "Lỗi", str(e))

    # ===== DASHBOARD =====
    def update_dashboard(self):
        stats = self.db.get_statistics()
        self.total_rooms_label.setText(f"Tổng phòng: {stats['total_rooms']}")
        self.empty_rooms_label.setText(f"Phòng trống: {stats['empty_rooms']}")
        self.total_residents_label.setText(f"Tổng cư dân: {stats['total_residents']}")
        self.refresh_rooms_table()
        self.refresh_residents_table()
        self.load_bill_combos()
        self._refresh_log_rooms_table()
        self._refresh_expenses_table()


def main():
    app = QApplication(sys.argv)
    window = RoomManagementApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
