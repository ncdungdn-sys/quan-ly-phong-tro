import sys
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTabWidget, QTableWidget, QTableWidgetItem,
                             QPushButton, QLabel, QLineEdit, QSpinBox, QDateEdit,
                             QDialog, QFormLayout, QMessageBox, QComboBox,
                             QDoubleSpinBox, QGroupBox, QTextEdit)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont
from database import Database

class RoomManagementApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("📁 Quản Lý Phòng Trọ")
        self.setGeometry(100, 100, 1200, 700)
        
        # Tạo widget chính
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout chính
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
        tabs.addTab(self.create_residents_tab(), "👥 Cư Dân")
        tabs.addTab(self.create_rooms_tab(), "🏘️ Phòng")
        tabs.addTab(self.create_bills_tab(), "📋 Hóa Đơn")
        tabs.addTab(self.create_electricity_tab(), "⚡ Điện")
        tabs.addTab(self.create_laundry_tab(), "👔 Giặt")
        tabs.addTab(self.create_expenses_tab(), "💰 Chi Phí")
        tabs.addTab(self.create_reports_tab(), "📊 Báo Cáo")
        
        main_layout.addWidget(tabs)
        central_widget.setLayout(main_layout)
        
        self.update_dashboard()
    
    def create_residents_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Nút thêm cư dân
        add_button = QPushButton("➕ Thêm Cư Dân")
        add_button.clicked.connect(self.add_resident_dialog)
        layout.addWidget(add_button)
        
        # Bảng cư dân
        self.residents_table = QTableWidget()
        self.residents_table.setColumnCount(7)
        self.residents_table.setHorizontalHeaderLabels(["ID", "Tên", "Tuổi", "CCCD", "SĐT", "Phòng", "Ngày Vào"])
        layout.addWidget(self.residents_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_rooms_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Nút thêm phòng
        add_button = QPushButton("➕ Thêm Phòng")
        add_button.clicked.connect(self.add_room_dialog)
        layout.addWidget(add_button)
        
        # Bảng phòng
        self.rooms_table = QTableWidget()
        self.rooms_table.setColumnCount(5)
        self.rooms_table.setHorizontalHeaderLabels(["Phòng", "Giá", "Trạng Thái", "Cư Dân", "Thao Tác"])
        self.rooms_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.rooms_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_bills_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        # --- Selector row ---
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("🏠 Phòng:"))
        self.bill_room_combo = QComboBox()
        self.bill_room_combo.currentIndexChanged.connect(self.on_bill_selector_changed)
        selector_layout.addWidget(self.bill_room_combo)

        selector_layout.addWidget(QLabel("  📅 Tháng:"))
        self.bill_month = QDateEdit()
        self.bill_month.setDate(QDate.currentDate())
        self.bill_month.setDisplayFormat("MM/yyyy")
        self.bill_month.dateChanged.connect(self.on_bill_selector_changed)
        selector_layout.addWidget(self.bill_month)
        selector_layout.addStretch()
        layout.addLayout(selector_layout)

        # --- Content area (2 columns) ---
        content_layout = QHBoxLayout()

        # --- Left: fee inputs ---
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

        # --- Right: Bill preview + payment ---
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
    
    def create_electricity_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Form ghi mốc điện
        form_layout = QFormLayout()
        self.elec_room_combo = QComboBox()
        self.elec_month = QDateEdit()
        self.elec_month.setDate(QDate.currentDate())
        self.elec_reading = QDoubleSpinBox()
        
        form_layout.addRow("Phòng:", self.elec_room_combo)
        form_layout.addRow("Tháng:", self.elec_month)
        form_layout.addRow("Mốc Điện:", self.elec_reading)
        
        layout.addLayout(form_layout)
        
        # Nút lưu
        save_button = QPushButton("💾 Lưu Mốc Điện")
        save_button.clicked.connect(self.save_electricity)
        layout.addWidget(save_button)
        
        # Bảng điện
        self.electricity_table = QTableWidget()
        self.electricity_table.setColumnCount(4)
        self.electricity_table.setHorizontalHeaderLabels(["Phòng", "Tháng", "Mốc", "Tiền Điện"])
        layout.addWidget(self.electricity_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_laundry_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("📋 Quản Lý Giặt Quần Áo"))
        
        # Bảng giặt
        self.laundry_table = QTableWidget()
        self.laundry_table.setColumnCount(4)
        self.laundry_table.setHorizontalHeaderLabels(["Phòng", "Số Người", "Tiền Giặt", "Tháng"])
        layout.addWidget(self.laundry_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_expenses_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Nút thêm chi phí
        add_button = QPushButton("➕ Thêm Chi Phí")
        add_button.clicked.connect(self.add_expense_dialog)
        layout.addWidget(add_button)
        
        # Bảng chi phí
        self.expenses_table = QTableWidget()
        self.expenses_table.setColumnCount(5)
        self.expenses_table.setHorizontalHeaderLabels(["Loại", "Mô Tả", "Số Tiền", "Phòng", "Ngày"])
        layout.addWidget(self.expenses_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_reports_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Nút xuất báo cáo
        export_button = QPushButton("📊 Xuất Báo Cáo Excel")
        export_button.clicked.connect(self.export_report)
        layout.addWidget(export_button)
        
        # Bảng báo cáo
        self.reports_table = QTableWidget()
        self.reports_table.setColumnCount(5)
        self.reports_table.setHorizontalHeaderLabels(["Tháng", "Doanh Thu", "Chi Phí", "Lợi Nhuận", "% Lợi Nhuận"])
        layout.addWidget(self.reports_table)
        
        widget.setLayout(layout)
        return widget
    
    def add_resident_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Thêm Cư Dân")
        dialog.setGeometry(100, 100, 400, 300)
        
        form_layout = QFormLayout()
        
        name_input = QLineEdit()
        age_input = QSpinBox()
        cccd_input = QLineEdit()
        phone_input = QLineEdit()
        room_combo = QComboBox()
        date_input = QDateEdit()
        date_input.setDate(QDate.currentDate())
        
        # Lấy danh sách tất cả phòng
        rooms = self.db.get_all_rooms()
        for room in rooms:
            room_combo.addItem(room['name'], room['id'])
        
        form_layout.addRow("Tên:", name_input)
        form_layout.addRow("Tuổi:", age_input)
        form_layout.addRow("CCCD:", cccd_input)
        form_layout.addRow("SĐT:", phone_input)
        form_layout.addRow("Phòng:", room_combo)
        form_layout.addRow("Ngày Vào:", date_input)
        
        save_button = QPushButton("Lưu")

        def do_save():
            try:
                self.db.add_resident(
                    name_input.text(), age_input.value(), cccd_input.text(),
                    phone_input.text(), room_combo.currentData(),
                    date_input.date().toString("yyyy-MM-dd")
                )
                dialog.accept()
                QMessageBox.information(self, "Thành công", "Cư dân đã được thêm!")
                self.update_dashboard()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", str(e))

        save_button.clicked.connect(do_save)
        form_layout.addRow(save_button)
        
        dialog.setLayout(form_layout)
        dialog.exec_()
    
    def save_resident(self, name, age, cccd, phone, room_id, date):
        try:
            self.db.add_resident(name, age, cccd, phone, room_id, date.toString("yyyy-MM-dd"))
            QMessageBox.information(self, "Thành công", "Cư dân đã được thêm!")
            self.update_dashboard()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e))
    
    def add_room_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Thêm Phòng")
        dialog.setGeometry(100, 100, 300, 200)
        
        form_layout = QFormLayout()
        
        room_name = QLineEdit()
        room_price = QDoubleSpinBox()
        room_price.setMaximum(10000000)
        
        form_layout.addRow("Tên Phòng:", room_name)
        form_layout.addRow("Giá Phòng:", room_price)
        
        save_button = QPushButton("Lưu")

        def do_save():
            try:
                self.db.add_room(room_name.text(), room_price.value())
                dialog.accept()
                QMessageBox.information(self, "Thành công", "Phòng đã được thêm!")
                self.update_dashboard()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", str(e))

        save_button.clicked.connect(do_save)
        form_layout.addRow(save_button)
        
        dialog.setLayout(form_layout)
        dialog.exec_()
    
    def save_room(self, name, price):
        try:
            self.db.add_room(name, price)
            QMessageBox.information(self, "Thành công", "Phòng đã được thêm!")
            self.update_dashboard()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e))
    
    def add_expense_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Thêm Chi Phí")
        dialog.setGeometry(100, 100, 400, 250)
        
        form_layout = QFormLayout()
        
        expense_type = QComboBox()
        expense_type.addItems(["Sửa Chữa Chung", "Bảo Trì", "Chi Phí Phòng"])
        expense_desc = QLineEdit()
        expense_amount = QDoubleSpinBox()
        expense_amount.setMaximum(10000000)
        
        form_layout.addRow("Loại Chi Phí:", expense_type)
        form_layout.addRow("Mô Tả:", expense_desc)
        form_layout.addRow("Số Tiền:", expense_amount)
        
        save_button = QPushButton("Lưu")

        def do_save():
            try:
                self.db.add_expense(
                    expense_type.currentText(), expense_desc.text(), expense_amount.value()
                )
                dialog.accept()
                QMessageBox.information(self, "Thành công", "Chi phí đã được thêm!")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", str(e))

        save_button.clicked.connect(do_save)
        form_layout.addRow(save_button)
        
        dialog.setLayout(form_layout)
        dialog.exec_()
    
    def save_expense(self, exp_type, description, amount):
        try:
            self.db.add_expense(exp_type, description, amount)
            QMessageBox.information(self, "Thành công", "Chi phí đã được thêm!")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e))
    
    def save_electricity(self):
        room_id = self.elec_room_combo.currentData()
        if not room_id:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn phòng!")
            return
        month = self.elec_month.date().toString("yyyy-MM-01")
        reading = self.elec_reading.value()
        try:
            self.db.add_electricity_reading(room_id, month, reading)
            QMessageBox.information(self, "Lưu", "Mốc điện đã được lưu!")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e))
    
    def export_report(self):
        QMessageBox.information(self, "Xuất", "Báo cáo đang được xuất...")

    # ===== PHÒNG =====

    def load_rooms(self):
        """Load danh sách phòng vào bảng"""
        rooms = self.db.get_all_rooms()
        self.rooms_table.setRowCount(len(rooms))
        for i, room in enumerate(rooms):
            residents = self.db.get_residents_by_room(room['id'])
            resident_names = (
                ', '.join([r['name'] for r in residents]) if residents else 'Trống'
            )
            self.rooms_table.setItem(i, 0, QTableWidgetItem(room['name']))
            self.rooms_table.setItem(i, 1, QTableWidgetItem(f"{room['price']:,.0f}đ"))
            status_text = "Có người" if room['status'] == 'occupied' else "Trống"
            self.rooms_table.setItem(i, 2, QTableWidgetItem(status_text))
            self.rooms_table.setItem(i, 3, QTableWidgetItem(resident_names))

            delete_btn = QPushButton("🗑️ Xóa")
            delete_btn.setStyleSheet("background-color: #dc3545; color: white;")
            delete_btn.clicked.connect(
                lambda checked, rid=room['id'], rname=room['name']:
                self.delete_room_action(rid, rname)
            )
            self.rooms_table.setCellWidget(i, 4, delete_btn)

    def delete_room_action(self, room_id, room_name):
        """Xóa phòng kèm xác nhận"""
        msg = QMessageBox(self)
        msg.setWindowTitle("Xác Nhận Xóa Phòng")
        msg.setText(f"Bạn có chắc muốn xóa phòng '{room_name}'?")
        msg.setInformativeText("⚠️ Tất cả cư dân trong phòng cũng sẽ bị xóa!")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        if msg.exec_() == QMessageBox.Yes:
            try:
                self.db.delete_room(room_id)
                QMessageBox.information(
                    self, "Thành công",
                    f"Đã xóa phòng '{room_name}' và tất cả cư dân liên quan!"
                )
                self.update_dashboard()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", str(e))

    # ===== CƯ DÂN =====

    def load_residents(self):
        """Load danh sách cư dân vào bảng"""
        residents = self.db.get_all_residents()
        self.residents_table.setRowCount(len(residents))
        for i, r in enumerate(residents):
            self.residents_table.setItem(i, 0, QTableWidgetItem(str(r['id'])))
            self.residents_table.setItem(i, 1, QTableWidgetItem(r['name'] or ''))
            self.residents_table.setItem(i, 2, QTableWidgetItem(str(r['age'] or '')))
            self.residents_table.setItem(i, 3, QTableWidgetItem(r['cccd'] or ''))
            self.residents_table.setItem(i, 4, QTableWidgetItem(r['phone'] or ''))
            self.residents_table.setItem(i, 5, QTableWidgetItem(r['room_name'] or ''))
            self.residents_table.setItem(i, 6, QTableWidgetItem(r['check_in_date'] or ''))

    # ===== HÓA ĐƠN =====

    def load_bill_combos(self):
        """Load danh sách phòng vào combo hóa đơn và điện"""
        rooms = self.db.get_all_rooms()

        # Billing tab combo
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

        # Electricity tab combo
        self.elec_room_combo.blockSignals(True)
        self.elec_room_combo.clear()
        for room in rooms:
            self.elec_room_combo.addItem(room['name'], room['id'])
        self.elec_room_combo.blockSignals(False)

        self.update_bill_preview()

    def on_bill_selector_changed(self):
        """Cập nhật xem trước khi đổi phòng/tháng"""
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

    def update_dashboard(self):
        stats = self.db.get_statistics()
        self.total_rooms_label.setText(f"Tổng phòng: {stats['total_rooms']}")
        self.empty_rooms_label.setText(f"Phòng trống: {stats['empty_rooms']}")
        self.total_residents_label.setText(f"Tổng cư dân: {stats['total_residents']}")
        self.load_rooms()
        self.load_residents()
        self.load_bill_combos()

def main():
    app = QApplication(sys.argv)
    window = RoomManagementApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
