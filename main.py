import sys
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTabWidget, QTableWidget, QTableWidgetItem,
                             QPushButton, QLabel, QLineEdit, QSpinBox, QDateEdit,
                             QDialog, QFormLayout, QMessageBox, QComboBox,
                             QDoubleSpinBox, QGroupBox, QFrame, QHeaderView)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QTextDocument
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from database import Database


class RoomManagementApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.init_ui()
        self.load_all_data()

    def init_ui(self):
        self.setWindowTitle("📁 Quản Lý Phòng Trọ")
        self.setGeometry(100, 100, 1200, 750)

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
        for lbl in [self.total_rooms_label, self.empty_rooms_label, self.total_residents_label]:
            lbl.setStyleSheet(
                "font-size: 13px; padding: 6px 12px; background: #E8F5E9; border-radius: 4px;"
            )
        dashboard_layout.addWidget(self.total_rooms_label)
        dashboard_layout.addWidget(self.empty_rooms_label)
        dashboard_layout.addWidget(self.total_residents_label)
        dashboard_layout.addStretch()
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

    # ===== TAB CƯ DÂN =====
    def create_residents_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("➕ Thêm Cư Dân")
        add_btn.clicked.connect(self.add_resident_dialog)
        del_btn = QPushButton("🗑️ Xóa Cư Dân")
        del_btn.clicked.connect(self.delete_resident)
        return_dep_btn = QPushButton("💰 Trả Cọc")
        return_dep_btn.clicked.connect(self.return_deposit_dialog)
        return_dep_btn.setStyleSheet("background-color: #FF8F00; color: white; padding: 6px;")
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addWidget(return_dep_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.residents_table = QTableWidget()
        self.residents_table.setColumnCount(8)
        self.residents_table.setHorizontalHeaderLabels([
            "ID", "Tên", "Tuổi", "CCCD", "SĐT", "Phòng", "Ngày Bắt Đầu Ở", "Đặt Cọc (đ)"
        ])
        self.residents_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.residents_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.residents_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.residents_table)

        widget.setLayout(layout)
        return widget

    # ===== TAB PHÒNG =====
    def create_rooms_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        add_btn = QPushButton("➕ Thêm Phòng")
        add_btn.clicked.connect(self.add_room_dialog)
        layout.addWidget(add_btn)

        self.rooms_table = QTableWidget()
        self.rooms_table.setColumnCount(4)
        self.rooms_table.setHorizontalHeaderLabels(["Phòng", "Giá (đ/tháng)", "Trạng Thái", "Cư Dân"])
        self.rooms_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.rooms_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.rooms_table)

        widget.setLayout(layout)
        return widget

    # ===== TAB HÓA ĐƠN =====
    def create_bills_tab(self):
        widget = QWidget()
        layout = QHBoxLayout()

        # ---- Cột trái: form tính tiền ----
        left_widget = QWidget()
        left_widget.setMaximumWidth(430)
        left_layout = QVBoxLayout()

        # Nhóm chọn phòng và thời gian
        room_group = QGroupBox("📋 Chọn Phòng & Thời Gian")
        room_form = QFormLayout()

        self.billing_room_combo = QComboBox()
        self.billing_room_combo.currentIndexChanged.connect(self.on_billing_room_changed)

        self.billing_resident_label = QLabel("—")
        self.billing_checkin_label = QLabel("—")

        self.billing_date_edit = QDateEdit()
        self.billing_date_edit.setDate(QDate.currentDate())
        self.billing_date_edit.setCalendarPopup(True)
        self.billing_date_edit.dateChanged.connect(self.calculate_room_fee)

        room_form.addRow("Phòng:", self.billing_room_combo)
        room_form.addRow("Cư Dân:", self.billing_resident_label)
        room_form.addRow("Ngày Bắt Đầu Ở:", self.billing_checkin_label)
        room_form.addRow("Ngày Tính Tiền:", self.billing_date_edit)
        room_group.setLayout(room_form)
        left_layout.addWidget(room_group)

        # Nhóm chi tiết chi phí
        fees_group = QGroupBox("💵 Chi Tiết Chi Phí")
        fees_form = QFormLayout()

        self.room_fee_label = QLabel("0 đ")
        self.room_fee_label.setStyleSheet("font-weight: bold; color: #1565C0;")

        self.elec_fee_input = QDoubleSpinBox()
        self.elec_fee_input.setMaximum(99999999)
        self.elec_fee_input.setSingleStep(1000)
        self.elec_fee_input.setSuffix(" đ")
        self.elec_fee_input.valueChanged.connect(self.update_bill_total)

        self.water_fee_input = QDoubleSpinBox()
        self.water_fee_input.setMaximum(99999999)
        self.water_fee_input.setSingleStep(1000)
        self.water_fee_input.setSuffix(" đ")
        self.water_fee_input.valueChanged.connect(self.update_bill_total)

        self.laundry_fee_input = QDoubleSpinBox()
        self.laundry_fee_input.setMaximum(99999999)
        self.laundry_fee_input.setSingleStep(1000)
        self.laundry_fee_input.setSuffix(" đ")
        self.laundry_fee_input.valueChanged.connect(self.update_bill_total)

        self.other_fee_input = QDoubleSpinBox()
        self.other_fee_input.setMaximum(99999999)
        self.other_fee_input.setSingleStep(1000)
        self.other_fee_input.setSuffix(" đ")
        self.other_fee_input.valueChanged.connect(self.update_bill_total)

        fees_form.addRow("Tiền Phòng:", self.room_fee_label)
        fees_form.addRow("Tiền Điện:", self.elec_fee_input)
        fees_form.addRow("Tiền Nước:", self.water_fee_input)
        fees_form.addRow("Tiền Giặt:", self.laundry_fee_input)
        fees_form.addRow("Chi Phí Khác:", self.other_fee_input)
        fees_group.setLayout(fees_form)
        left_layout.addWidget(fees_group)

        # Tổng cộng
        total_group = QGroupBox("💰 Tổng Cộng")
        total_layout = QVBoxLayout()
        self.bill_total_label = QLabel("TỔNG HÓA ĐƠN: 0 đ")
        total_font = QFont()
        total_font.setPointSize(13)
        total_font.setBold(True)
        self.bill_total_label.setFont(total_font)
        self.bill_total_label.setStyleSheet("color: #C62828; padding: 8px;")
        total_layout.addWidget(self.bill_total_label)
        total_group.setLayout(total_layout)
        left_layout.addWidget(total_group)

        # Các nút thao tác
        calc_btn = QPushButton("🔄 Tính Lại Tiền Phòng")
        calc_btn.clicked.connect(self.calculate_room_fee)

        print_btn = QPushButton("🖨️ In Hóa Đơn")
        print_btn.clicked.connect(self.print_bill)
        print_btn.setStyleSheet(
            "background-color: #1565C0; color: white; padding: 8px; font-size: 13px; font-weight: bold;"
        )

        save_bill_btn = QPushButton("💾 Lưu Hóa Đơn")
        save_bill_btn.clicked.connect(self.save_current_bill)

        left_layout.addWidget(calc_btn)
        left_layout.addWidget(print_btn)
        left_layout.addWidget(save_bill_btn)
        left_layout.addStretch()

        left_widget.setLayout(left_layout)
        layout.addWidget(left_widget)

        # Đường phân cách
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep)

        # ---- Cột phải: lịch sử hóa đơn ----
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("📋 Lịch Sử Hóa Đơn"))

        self.bills_table = QTableWidget()
        self.bills_table.setColumnCount(7)
        self.bills_table.setHorizontalHeaderLabels([
            "Phòng", "Cư Dân", "Ngày Tính", "Tiền Phòng",
            "Dịch Vụ", "Tổng Tiền", "Trạng Thái"
        ])
        self.bills_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.bills_table.setEditTriggers(QTableWidget.NoEditTriggers)
        right_layout.addWidget(self.bills_table)

        right_widget.setLayout(right_layout)
        layout.addWidget(right_widget)

        widget.setLayout(layout)
        return widget

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

        add_button = QPushButton("➕ Thêm Chi Phí")
        add_button.clicked.connect(self.add_expense_dialog)
        layout.addWidget(add_button)

        self.expenses_table = QTableWidget()
        self.expenses_table.setColumnCount(5)
        self.expenses_table.setHorizontalHeaderLabels(["Loại", "Mô Tả", "Số Tiền", "Phòng", "Ngày"])
        self.expenses_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.expenses_table)

        widget.setLayout(layout)
        return widget

    # ===== TAB BÁO CÁO =====
    def create_reports_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        export_button = QPushButton("📊 Xuất Báo Cáo Excel")
        export_button.clicked.connect(self.export_report)
        layout.addWidget(export_button)

        self.reports_table = QTableWidget()
        self.reports_table.setColumnCount(5)
        self.reports_table.setHorizontalHeaderLabels(["Tháng", "Doanh Thu", "Chi Phí", "Lợi Nhuận", "% Lợi Nhuận"])
        self.reports_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.reports_table)

        widget.setLayout(layout)
        return widget

    # ===== XỬ LÝ CƯ DÂN =====
    def add_resident_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Thêm Cư Dân")
        dialog.setGeometry(200, 150, 420, 380)

        form_layout = QFormLayout()

        name_input = QLineEdit()
        age_input = QSpinBox()
        age_input.setRange(1, 150)
        cccd_input = QLineEdit()
        phone_input = QLineEdit()
        room_combo = QComboBox()

        date_input = QDateEdit()
        date_input.setDate(QDate.currentDate())
        date_input.setCalendarPopup(True)

        deposit_input = QDoubleSpinBox()
        deposit_input.setMaximum(100000000)
        deposit_input.setSingleStep(100000)
        deposit_input.setSuffix(" đ")

        rooms = self.db.get_empty_rooms()
        for room_id, room_name in rooms:
            room_combo.addItem(room_name, room_id)

        if not rooms:
            room_combo.addItem("— Không có phòng trống —", None)

        form_layout.addRow("Tên:", name_input)
        form_layout.addRow("Tuổi:", age_input)
        form_layout.addRow("CCCD:", cccd_input)
        form_layout.addRow("SĐT:", phone_input)
        form_layout.addRow("Phòng:", room_combo)
        form_layout.addRow("Ngày Bắt Đầu Ở:", date_input)
        form_layout.addRow("Đặt Cọc:", deposit_input)

        save_btn = QPushButton("💾 Lưu")
        save_btn.clicked.connect(lambda: self.save_resident(
            name_input.text(), age_input.value(), cccd_input.text(),
            phone_input.text(), room_combo.currentData(),
            date_input.date(), deposit_input.value(), dialog
        ))
        form_layout.addRow(save_btn)

        dialog.setLayout(form_layout)
        dialog.exec_()

    def save_resident(self, name, age, cccd, phone, room_id, qdate, dat_coc, dialog):
        if not name.strip():
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên cư dân!")
            return
        if room_id is None:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn phòng!")
            return
        try:
            self.db.add_resident(
                name, age, cccd, phone, room_id,
                qdate.toString("yyyy-MM-dd"), dat_coc
            )
            QMessageBox.information(self, "Thành công", "Cư dân đã được thêm!")
            dialog.close()
            self.load_all_data()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e))

    def delete_resident(self):
        selected = self.residents_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn cư dân cần xóa!")
            return
        row = self.residents_table.currentRow()
        resident_id = int(self.residents_table.item(row, 0).text())
        resident_name = self.residents_table.item(row, 1).text()

        reply = QMessageBox.question(
            self, "Xác Nhận", f"Xóa cư dân '{resident_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.delete_resident(resident_id)
            self.load_all_data()

    def return_deposit_dialog(self):
        selected = self.residents_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn cư dân!")
            return
        row = self.residents_table.currentRow()
        resident_name = self.residents_table.item(row, 1).text()
        deposit_item = self.residents_table.item(row, 7)

        try:
            deposit = float(deposit_item.data(Qt.UserRole) or 0)
        except Exception:
            deposit = 0

        if deposit <= 0:
            QMessageBox.information(self, "Thông Báo", "Cư dân này không có tiền đặt cọc!")
            return

        formatted = f"{deposit:,.0f} đ"
        reply = QMessageBox.question(
            self, "Trả Cọc",
            f"Trả cọc cho cư dân: {resident_name}\nSố tiền: {formatted}\n\nXác nhận trả cọc?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            QMessageBox.information(
                self, "Thành Công",
                f"Đã trả cọc {formatted} cho {resident_name}!\n"
                f"Vui lòng xóa cư dân khỏi hệ thống khi họ rời đi."
            )

    # ===== XỬ LÝ PHÒNG =====
    def add_room_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Thêm Phòng")
        dialog.setGeometry(200, 150, 300, 200)

        form_layout = QFormLayout()

        room_name = QLineEdit()
        room_price = QDoubleSpinBox()
        room_price.setMaximum(100000000)
        room_price.setSingleStep(100000)
        room_price.setSuffix(" đ")

        form_layout.addRow("Tên Phòng:", room_name)
        form_layout.addRow("Giá Phòng/tháng:", room_price)

        save_button = QPushButton("💾 Lưu")
        save_button.clicked.connect(lambda: self.save_room(room_name.text(), room_price.value(), dialog))
        form_layout.addRow(save_button)

        dialog.setLayout(form_layout)
        dialog.exec_()

    def save_room(self, name, price, dialog):
        if not name.strip():
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên phòng!")
            return
        try:
            self.db.add_room(name, price)
            QMessageBox.information(self, "Thành công", "Phòng đã được thêm!")
            dialog.close()
            self.load_all_data()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e))

    # ===== XỬ LÝ HÓA ĐƠN =====
    def on_billing_room_changed(self, index):
        if index < 0:
            return
        room_id = self.billing_room_combo.currentData()
        if room_id is None:
            self.billing_resident_label.setText("—")
            self.billing_checkin_label.setText("—")
            self.room_fee_label.setText("0 đ")
            return

        resident = self.db.get_resident_by_room(room_id)
        if resident:
            self.billing_resident_label.setText(resident['name'])
            check_in = resident['check_in_date']
            try:
                d = datetime.strptime(check_in, '%Y-%m-%d')
                self.billing_checkin_label.setText(d.strftime('%d/%m/%Y'))
            except Exception:
                self.billing_checkin_label.setText(str(check_in))
            self.calculate_room_fee()
        else:
            self.billing_resident_label.setText("—")
            self.billing_checkin_label.setText("—")
            self.room_fee_label.setText("0 đ")
            self.update_bill_total()

    def calculate_room_fee(self):
        room_id = self.billing_room_combo.currentData()
        if room_id is None:
            return

        resident = self.db.get_resident_by_room(room_id)
        if not resident:
            return

        check_in = resident['check_in_date']
        billing_date = self.billing_date_edit.date().toPyDate()
        fee = self.db.calculate_room_fee_by_days(room_id, check_in, billing_date)
        self.room_fee_label.setText(f"{fee:,.0f} đ")
        self.update_bill_total()

    def _parse_room_fee(self):
        """Đọc giá trị tiền phòng từ label (bỏ dấu phẩy và ký hiệu đ)"""
        try:
            raw = self.room_fee_label.text().replace(',', '').replace(' đ', '').replace('đ', '').strip()
            return float(raw) if raw and raw != '—' else 0.0
        except Exception:
            return 0.0

    def update_bill_total(self):
        total = (self._parse_room_fee()
                 + self.elec_fee_input.value()
                 + self.water_fee_input.value()
                 + self.laundry_fee_input.value()
                 + self.other_fee_input.value())
        self.bill_total_label.setText(f"TỔNG HÓA ĐƠN: {total:,.0f} đ")

    def _get_current_bill_data(self):
        """Trả về dict chứa dữ liệu hóa đơn hiện tại"""
        room_id = self.billing_room_combo.currentData()
        room_name = self.billing_room_combo.currentText()
        resident_name = self.billing_resident_label.text()
        check_in_display = self.billing_checkin_label.text()
        billing_date_display = self.billing_date_edit.date().toString("dd/MM/yyyy")
        billing_date_iso = self.billing_date_edit.date().toString("yyyy-MM-dd")

        try:
            room_fee = self._parse_room_fee()
        except Exception:
            room_fee = 0.0

        elec = self.elec_fee_input.value()
        water = self.water_fee_input.value()
        laundry = self.laundry_fee_input.value()
        other = self.other_fee_input.value()
        total = room_fee + elec + water + laundry + other

        return {
            'room_id': room_id,
            'room_name': room_name,
            'resident_name': resident_name,
            'check_in_display': check_in_display,
            'billing_date_display': billing_date_display,
            'billing_date_iso': billing_date_iso,
            'room_fee': room_fee,
            'electricity_fee': elec,
            'water_fee': water,
            'laundry_fee': laundry,
            'other_fees': other,
            'total': total,
        }

    def print_bill(self):
        data = self._get_current_bill_data()
        if not data['room_id'] or data['resident_name'] == '—':
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn phòng trước khi in!")
            return

        html = self._build_bill_html(data)
        printer = QPrinter(QPrinter.HighResolution)
        dlg = QPrintDialog(printer, self)
        if dlg.exec_() == QPrintDialog.Accepted:
            doc = QTextDocument()
            doc.setHtml(html)
            doc.print_(printer)

    def _build_bill_html(self, data):
        # Service fee rows: (HTML-encoded label, data key)
        service_fields = [
            ("Ti&#x1EC1;n &#x110;i&#x1EC7;n", 'electricity_fee'),
            ("Ti&#x1EC1;n N&#x01B0;&#x1EDB;c", 'water_fee'),
            ("Ti&#x1EC1;n Gi&#x1EB7;t", 'laundry_fee'),
            ("Chi Ph&#xED; Kh&#xE1;c", 'other_fees'),
        ]
        rows = [
            f"<tr><td>{label}:</td><td align='right'><b>{data[key]:,.0f} &#x111;</b></td></tr>"
            for label, key in service_fields
            if data[key] > 0
        ]
        service_rows = '\n'.join(rows)

        return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: Arial, sans-serif; font-size: 13px; max-width: 420px; margin: 20px auto;">
<h2 style="text-align:center; letter-spacing:2px; margin-bottom:4px;">
  H&#xD3;A &#x110;&#x1EB6;N TI&#x1EC0;N PH&#xD2;NG
</h2>
<hr style="border:2px solid #333; margin:6px 0;">
<table width="100%" cellpadding="4">
  <tr><td><b>Ph&#xF2;ng:</b></td><td>{data['room_name']}</td></tr>
  <tr><td><b>C&#x01B0; D&#xE2;n:</b></td><td>{data['resident_name']}</td></tr>
  <tr><td><b>Ng&#xE0;y v&#xE0;o:</b></td><td>{data['check_in_display']}</td></tr>
  <tr><td><b>Ng&#xE0;y t&#xED;nh:</b></td><td>{data['billing_date_display']}</td></tr>
</table>
<hr style="border:1px solid #888; margin:6px 0;">
<h3 style="text-align:center; margin:4px 0;">CHI TI&#x1EBE;T</h3>
<table width="100%" cellpadding="4">
  <tr><td>Ti&#x1EC1;n Ph&#xF2;ng:</td><td align='right'><b>{data['room_fee']:,.0f} &#x111;</b></td></tr>
  {service_rows}
</table>
<hr style="border:2px solid #333; margin:6px 0;">
<h3 style="text-align:center; color:#C62828;">
  T&#x1ED4;NG H&#xD3;A &#x110;&#x1EB6;N: {data['total']:,.0f} &#x111;
</h3>
<hr style="border:2px solid #333; margin:6px 0;">
<p style="text-align:center; font-style:italic; margin-top:8px;">C&#x1EA3;m &#x1A1;n qu&#xFD; kh&#xE1;ch!</p>
</body>
</html>"""

    def save_current_bill(self):
        data = self._get_current_bill_data()
        if data['room_id'] is None or data['resident_name'] == '—':
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn phòng!")
            return

        resident = self.db.get_resident_by_room(data['room_id'])
        if not resident:
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy cư dân!")
            return

        try:
            self.db.save_bill(
                data['room_id'], resident['id'], data['billing_date_iso'],
                data['room_fee'], data['electricity_fee'],
                data['water_fee'], data['laundry_fee'], data['other_fees']
            )
            QMessageBox.information(self, "Thành Công", "Đã lưu hóa đơn!")
            self.load_bills_table()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e))

    # ===== XỬ LÝ ĐIỆN =====
    def save_electricity(self):
        QMessageBox.information(self, "Lưu", "Mốc điện đã được lưu!")

    # ===== XỬ LÝ CHI PHÍ =====
    def add_expense_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Thêm Chi Phí")
        dialog.setGeometry(200, 150, 400, 250)

        form_layout = QFormLayout()

        expense_type = QComboBox()
        expense_type.addItems(["Sửa Chữa Chung", "Bảo Trì", "Chi Phí Phòng"])
        expense_desc = QLineEdit()
        expense_amount = QDoubleSpinBox()
        expense_amount.setMaximum(100000000)
        expense_amount.setSuffix(" đ")

        form_layout.addRow("Loại Chi Phí:", expense_type)
        form_layout.addRow("Mô Tả:", expense_desc)
        form_layout.addRow("Số Tiền:", expense_amount)

        save_button = QPushButton("💾 Lưu")
        save_button.clicked.connect(lambda: self.save_expense(
            expense_type.currentText(), expense_desc.text(), expense_amount.value(), dialog
        ))
        form_layout.addRow(save_button)

        dialog.setLayout(form_layout)
        dialog.exec_()

    def save_expense(self, exp_type, description, amount, dialog):
        try:
            self.db.add_expense(exp_type, description, amount)
            QMessageBox.information(self, "Thành công", "Chi phí đã được thêm!")
            dialog.close()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e))

    # ===== BÁO CÁO =====
    def export_report(self):
        QMessageBox.information(self, "Xuất", "Báo cáo đang được xuất...")

    # ===== TẢI DỮ LIỆU =====
    def load_all_data(self):
        self.load_residents_table()
        self.load_rooms_table()
        self.load_bills_table()
        self.update_billing_room_combo()
        self.update_dashboard()

    def load_residents_table(self):
        residents = self.db.get_all_residents()
        self.residents_table.setRowCount(len(residents))
        for row, r in enumerate(residents):
            deposit = r['dat_coc'] if r['dat_coc'] else 0.0
            try:
                d = datetime.strptime(r['check_in_date'], '%Y-%m-%d')
                date_str = d.strftime('%d/%m/%Y')
            except Exception:
                date_str = r['check_in_date']

            items = [
                QTableWidgetItem(str(r['id'])),
                QTableWidgetItem(r['name']),
                QTableWidgetItem(str(r['age'] or '')),
                QTableWidgetItem(r['cccd'] or ''),
                QTableWidgetItem(r['phone'] or ''),
                QTableWidgetItem(r['room_name'] or ''),
                QTableWidgetItem(date_str),
                QTableWidgetItem(f"{deposit:,.0f}"),
            ]
            # Store raw deposit value for retrieval in return_deposit_dialog
            items[7].setData(Qt.UserRole, deposit)

            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignCenter)
                self.residents_table.setItem(row, col, item)

    def load_rooms_table(self):
        rooms = self.db.get_all_rooms_with_residents()
        self.rooms_table.setRowCount(len(rooms))
        for row, r in enumerate(rooms):
            status = "Có người" if r['status'] == 'occupied' else "Trống"
            items = [
                QTableWidgetItem(r['name']),
                QTableWidgetItem(f"{r['price']:,.0f}"),
                QTableWidgetItem(status),
                QTableWidgetItem(r['resident_name'] or ''),
            ]
            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignCenter)
                self.rooms_table.setItem(row, col, item)

    def load_bills_table(self):
        bills = self.db.get_all_bills()
        self.bills_table.setRowCount(len(bills))
        for row, b in enumerate(bills):
            service_total = (
                (b['electricity_fee'] or 0)
                + (b['water_fee'] or 0)
                + (b['laundry_fee'] or 0)
                + (b['other_fees'] or 0)
            )
            try:
                d = datetime.strptime(b['month'], '%Y-%m-%d')
                date_str = d.strftime('%d/%m/%Y')
            except Exception:
                date_str = b['month']

            paid_status = "Đã thanh toán" if b['paid'] else "Chưa thanh toán"
            items = [
                QTableWidgetItem(b['room_name']),
                QTableWidgetItem(b['resident_name']),
                QTableWidgetItem(date_str),
                QTableWidgetItem(f"{b['room_fee']:,.0f} đ"),
                QTableWidgetItem(f"{service_total:,.0f} đ"),
                QTableWidgetItem(f"{b['total_amount']:,.0f} đ"),
                QTableWidgetItem(paid_status),
            ]
            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignCenter)
                self.bills_table.setItem(row, col, item)

    def update_billing_room_combo(self):
        self.billing_room_combo.blockSignals(True)
        self.billing_room_combo.clear()
        rooms = self.db.get_occupied_rooms_with_residents()
        if not rooms:
            self.billing_room_combo.addItem("— Không có phòng nào —", None)
        else:
            for room in rooms:
                self.billing_room_combo.addItem(
                    f"{room['room_name']} ({room['resident_name']})",
                    room['room_id']
                )
        self.billing_room_combo.blockSignals(False)
        # Trigger update for the currently selected room
        if self.billing_room_combo.count() > 0:
            self.on_billing_room_changed(0)

    def update_dashboard(self):
        stats = self.db.get_statistics()
        self.total_rooms_label.setText(f"Tổng phòng: {stats['total_rooms']}")
        self.empty_rooms_label.setText(f"Phòng trống: {stats['empty_rooms']}")
        self.total_residents_label.setText(f"Tổng cư dân: {stats['total_residents']}")


def main():
    app = QApplication(sys.argv)
    window = RoomManagementApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
