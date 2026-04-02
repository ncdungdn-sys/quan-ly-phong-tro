import sys
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QLineEdit, QSpinBox, QDialog, QFormLayout, QMessageBox, QComboBox,
    QDoubleSpinBox, QSplitter, QGroupBox, QTextEdit, QHeaderView,
    QAbstractItemView, QScrollArea, QFileDialog,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from database import Database


def fmt_currency(amount):
    """Định dạng tiền tệ kiểu Việt Nam"""
    if not amount:
        return "0đ"
    return f"{int(amount):,}đ".replace(",", ".")


# ─────────────────────────────────────────────
#  Dialog: Thêm / Sửa Phòng
# ─────────────────────────────────────────────

class RoomDialog(QDialog):
    def __init__(self, parent, room=None):
        super().__init__(parent)
        self.room = room
        self.setWindowTitle("Thêm Phòng" if room is None else "Sửa Phòng")
        self.setFixedWidth(420)
        self._setup_ui()

    def _setup_ui(self):
        layout = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("VD: P101, P102…")

        self.price_input = QDoubleSpinBox()
        self.price_input.setMaximum(99_000_000)
        self.price_input.setSingleStep(100_000)
        self.price_input.setDecimals(0)
        self.price_input.setSuffix(" đ")

        self.start_date_input = QLineEdit()
        self.start_date_input.setPlaceholderText("DD/MM/YYYY")

        self.deposit_input = QDoubleSpinBox()
        self.deposit_input.setMaximum(99_000_000)
        self.deposit_input.setSingleStep(500_000)
        self.deposit_input.setDecimals(0)
        self.deposit_input.setSuffix(" đ")

        self.billing_day_input = QSpinBox()
        self.billing_day_input.setMinimum(1)
        self.billing_day_input.setMaximum(31)
        self.billing_day_input.setValue(1)

        self.notes_input = QLineEdit()

        layout.addRow("Tên Phòng: *", self.name_input)
        layout.addRow("Giá Phòng (đ/tháng):", self.price_input)
        layout.addRow("Ngày Bắt Đầu Ở:", self.start_date_input)
        layout.addRow("Đặt Cọc:", self.deposit_input)
        layout.addRow("Ngày Tính Tiền (hàng tháng):", self.billing_day_input)
        layout.addRow("Ghi Chú:", self.notes_input)

        if self.room:
            self.name_input.setText(self.room['name'] or '')
            self.price_input.setValue(self.room['price'] or 0)
            start = self.room['start_date']
            if start:
                try:
                    self.start_date_input.setText(
                        datetime.strptime(start, '%Y-%m-%d').strftime('%d/%m/%Y')
                    )
                except ValueError:
                    self.start_date_input.setText(start)
            self.deposit_input.setValue(self.room['deposit'] or 0)
            self.billing_day_input.setValue(self.room['billing_day'] or 1)
            self.notes_input.setText(self.room['notes'] or '')

        btn_row = QHBoxLayout()
        save_btn = QPushButton("✅ Lưu")
        cancel_btn = QPushButton("❌ Hủy")
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        w = QWidget()
        w.setLayout(btn_row)
        layout.addRow(w)

        self.setLayout(layout)

    def get_data(self):
        name = self.name_input.text().strip()
        price = self.price_input.value()

        start_text = self.start_date_input.text().strip()
        start_date = None
        if start_text:
            for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
                try:
                    start_date = datetime.strptime(start_text, fmt).strftime('%Y-%m-%d')
                    break
                except ValueError:
                    pass

        deposit = self.deposit_input.value()
        billing_day = self.billing_day_input.value()
        notes = self.notes_input.text().strip()
        return name, price, start_date, deposit, billing_day, notes


# ─────────────────────────────────────────────
#  Dialog: Thêm / Sửa Khách Trọ
# ─────────────────────────────────────────────

class ResidentDialog(QDialog):
    def __init__(self, parent, room_id, resident=None):
        super().__init__(parent)
        self.room_id = room_id
        self.resident = resident
        self.setWindowTitle("Thêm Khách Trọ" if resident is None else "Sửa Khách Trọ")
        self.setFixedWidth(400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QFormLayout()

        self.name_input = QLineEdit()
        self.cccd_input = QLineEdit()
        self.dob_input = QLineEdit()
        self.dob_input.setPlaceholderText("DD/MM/YYYY")
        self.hometown_input = QLineEdit()
        self.phone_input = QLineEdit()

        layout.addRow("Tên khách trọ: *", self.name_input)
        layout.addRow("CCCD (không bắt buộc):", self.cccd_input)
        layout.addRow("Ngày Tháng Năm Sinh:", self.dob_input)
        layout.addRow("Quê Quán:", self.hometown_input)
        layout.addRow("Số Điện Thoại:", self.phone_input)

        if self.resident:
            self.name_input.setText(self.resident['name'] or '')
            self.cccd_input.setText(self.resident['cccd'] or '')
            dob = self.resident['date_of_birth']
            if dob:
                try:
                    self.dob_input.setText(
                        datetime.strptime(dob, '%Y-%m-%d').strftime('%d/%m/%Y')
                    )
                except ValueError:
                    self.dob_input.setText(dob)
            self.hometown_input.setText(self.resident['hometown'] or '')
            self.phone_input.setText(self.resident['phone'] or '')

        btn_row = QHBoxLayout()
        save_btn = QPushButton("✅ Lưu")
        cancel_btn = QPushButton("❌ Hủy")
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        w = QWidget()
        w.setLayout(btn_row)
        layout.addRow(w)

        self.setLayout(layout)

    def get_data(self):
        name = self.name_input.text().strip()
        cccd = self.cccd_input.text().strip() or None

        dob_text = self.dob_input.text().strip()
        dob = None
        if dob_text:
            for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
                try:
                    dob = datetime.strptime(dob_text, fmt).strftime('%Y-%m-%d')
                    break
                except ValueError:
                    pass

        hometown = self.hometown_input.text().strip() or None
        phone = self.phone_input.text().strip() or None
        return name, cccd, dob, hometown, phone


# ─────────────────────────────────────────────
#  Main Application Window
# ─────────────────────────────────────────────

class RoomManagementApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.selected_room_id = None
        self._init_ui()
        self._load_rooms()
        self._check_billing_notifications()

    # ── UI Setup ──────────────────────────────

    def _init_ui(self):
        self.setWindowTitle("🏠 Quản Lý Phòng Trọ")
        self.setGeometry(100, 100, 1280, 750)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout()
        central.setLayout(root)

        # ── Header / Dashboard ─────────────────
        header = QHBoxLayout()

        title = QLabel("🏠 HỆ THỐNG QUẢN LÝ PHÒNG TRỌ")
        f = QFont()
        f.setPointSize(14)
        f.setBold(True)
        title.setFont(f)
        header.addWidget(title)
        header.addStretch()

        self.lbl_total = QLabel("Tổng phòng: 0")
        self.lbl_occupied = QLabel("Có người: 0")
        self.lbl_guests = QLabel("Khách trọ: 0")
        badge_style = (
            "padding: 4px 10px; background:#e3f2fd; "
            "border-radius:4px; margin:2px;"
        )
        for lbl in (self.lbl_total, self.lbl_occupied, self.lbl_guests):
            lbl.setStyleSheet(badge_style)
            header.addWidget(lbl)

        export_btn = QPushButton("📊 Xuất DS Khách Trọ (Excel)")
        export_btn.setStyleSheet(
            "padding:4px 12px; background:#4CAF50; color:white; border-radius:4px;"
        )
        export_btn.clicked.connect(self._export_excel)
        header.addWidget(export_btn)

        root.addLayout(header)

        # ── Tabs ───────────────────────────────
        tabs = QTabWidget()
        tabs.addTab(self._create_rooms_tab(), "🏘️ Phòng")
        tabs.addTab(self._create_bills_tab(), "📋 Hóa Đơn")
        tabs.addTab(self._create_settings_tab(), "⚙️ Cài Đặt")
        root.addWidget(tabs)

    # ── Tab: Phòng ────────────────────────────

    def _create_rooms_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Action buttons
        btn_row = QHBoxLayout()
        add_btn = QPushButton("➕ Thêm Phòng")
        edit_btn = QPushButton("✏️ Sửa Phòng")
        del_btn = QPushButton("🗑️ Xóa Phòng")
        add_btn.clicked.connect(self._add_room)
        edit_btn.clicked.connect(self._edit_room)
        del_btn.clicked.connect(self._delete_room)
        for b in (add_btn, edit_btn, del_btn):
            btn_row.addWidget(b)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left: room list
        left = QWidget()
        ll = QVBoxLayout()
        ll.addWidget(QLabel("📋 Danh Sách Phòng"))
        self.rooms_table = QTableWidget()
        self.rooms_table.setColumnCount(6)
        self.rooms_table.setHorizontalHeaderLabels(
            ["Phòng", "Giá/Tháng", "Ngày Bắt Đầu", "Đặt Cọc", "Trạng Thái", "Khách"]
        )
        self.rooms_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.rooms_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.rooms_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.rooms_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.rooms_table.selectionModel().selectionChanged.connect(self._on_room_selected)
        ll.addWidget(self.rooms_table)
        left.setLayout(ll)

        # Right: residents
        right = QWidget()
        rl = QVBoxLayout()
        rl.addWidget(QLabel("👥 Khách Trọ Trong Phòng"))

        res_btn_row = QHBoxLayout()
        add_res_btn = QPushButton("➕ Thêm Khách")
        edit_res_btn = QPushButton("✏️ Sửa")
        del_res_btn = QPushButton("🗑️ Xóa")
        add_res_btn.clicked.connect(self._add_resident)
        edit_res_btn.clicked.connect(self._edit_resident)
        del_res_btn.clicked.connect(self._delete_resident)
        for b in (add_res_btn, edit_res_btn, del_res_btn):
            res_btn_row.addWidget(b)
        res_btn_row.addStretch()
        rl.addLayout(res_btn_row)

        self.residents_table = QTableWidget()
        self.residents_table.setColumnCount(5)
        self.residents_table.setHorizontalHeaderLabels(
            ["Tên", "CCCD", "Ngày Sinh", "Quê Quán", "SĐT"]
        )
        self.residents_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.residents_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.residents_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.residents_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        rl.addWidget(self.residents_table)
        right.setLayout(rl)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([540, 640])
        layout.addWidget(splitter)
        return widget

    # ── Tab: Hóa Đơn ─────────────────────────

    def _create_bills_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Selector row
        sel = QHBoxLayout()
        sel.addWidget(QLabel("Phòng:"))
        self.bill_room_combo = QComboBox()
        self.bill_room_combo.setMinimumWidth(120)
        sel.addWidget(self.bill_room_combo)

        sel.addWidget(QLabel("Tháng/Năm:"))
        self.bill_month_input = QLineEdit()
        self.bill_month_input.setPlaceholderText("MM/YYYY")
        now = datetime.now()
        self.bill_month_input.setText(f"{now.month:02d}/{now.year}")
        self.bill_month_input.setMaximumWidth(90)
        sel.addWidget(self.bill_month_input)

        load_btn = QPushButton("📂 Tải Dữ Liệu")
        load_btn.clicked.connect(self._load_bill_data)
        sel.addWidget(load_btn)
        sel.addStretch()
        layout.addLayout(sel)

        # Splitter: form | preview
        splitter = QSplitter(Qt.Horizontal)

        # ── Left: input form ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        form_widget = QWidget()
        form_layout = QVBoxLayout()

        # Electricity
        elec_grp = QGroupBox("⚡ Điện")
        elec_form = QFormLayout()
        self.elec_old = QDoubleSpinBox()
        self.elec_old.setMaximum(999_999)
        self.elec_old.setDecimals(0)
        self.elec_new = QDoubleSpinBox()
        self.elec_new.setMaximum(999_999)
        self.elec_new.setDecimals(0)
        self.elec_usage_lbl = QLabel("0 kWh")
        self.elec_fee_lbl = QLabel("0đ")
        for w in (self.elec_old, self.elec_new):
            w.valueChanged.connect(self._update_preview)
        elec_form.addRow("Số Cũ:", self.elec_old)
        elec_form.addRow("Số Mới:", self.elec_new)
        elec_form.addRow("Số Xài:", self.elec_usage_lbl)
        elec_form.addRow("Tiền Điện:", self.elec_fee_lbl)
        elec_grp.setLayout(elec_form)
        form_layout.addWidget(elec_grp)

        # Water
        water_grp = QGroupBox("💧 Nước")
        water_form = QFormLayout()
        self.water_old = QDoubleSpinBox()
        self.water_old.setMaximum(999_999)
        self.water_old.setDecimals(0)
        self.water_new = QDoubleSpinBox()
        self.water_new.setMaximum(999_999)
        self.water_new.setDecimals(0)
        self.water_usage_lbl = QLabel("0 khối")
        self.water_fee_lbl = QLabel("0đ")
        for w in (self.water_old, self.water_new):
            w.valueChanged.connect(self._update_preview)
        water_form.addRow("Số Cũ:", self.water_old)
        water_form.addRow("Số Mới:", self.water_new)
        water_form.addRow("Số Xài:", self.water_usage_lbl)
        water_form.addRow("Tiền Nước:", self.water_fee_lbl)
        water_grp.setLayout(water_form)
        form_layout.addWidget(water_grp)

        # Laundry
        laundry_grp = QGroupBox("👔 Giặt")
        laundry_form = QFormLayout()
        self.laundry_times = QSpinBox()
        self.laundry_times.setMaximum(999)
        self.laundry_amount = QDoubleSpinBox()
        self.laundry_amount.setMaximum(9_999_999)
        self.laundry_amount.setDecimals(0)
        self.laundry_amount.setSuffix(" đ")
        self.laundry_times.valueChanged.connect(self._on_laundry_times_changed)
        self.laundry_amount.valueChanged.connect(self._update_preview)
        laundry_form.addRow("Số Lần:", self.laundry_times)
        laundry_form.addRow("Tiền Giặt:", self.laundry_amount)
        laundry_grp.setLayout(laundry_form)
        form_layout.addWidget(laundry_grp)

        # Other expenses
        other_grp = QGroupBox("💰 Chi Phí Khác")
        other_form = QFormLayout()
        self.other_amount = QDoubleSpinBox()
        self.other_amount.setMaximum(99_999_999)
        self.other_amount.setDecimals(0)
        self.other_amount.setSuffix(" đ")
        self.other_notes = QLineEdit()
        self.other_notes.setPlaceholderText("Ghi chú (VD: Sửa cửa)")
        self.other_amount.valueChanged.connect(self._update_preview)
        other_form.addRow("Số Tiền:", self.other_amount)
        other_form.addRow("Ghi Chú:", self.other_notes)
        other_grp.setLayout(other_form)
        form_layout.addWidget(other_grp)

        # Buttons
        act_row = QHBoxLayout()
        save_btn = QPushButton("💾 Lưu Dữ Liệu")
        print_btn = QPushButton("🖨️ In Hóa Đơn")
        save_btn.setStyleSheet(
            "padding:6px; background:#2196F3; color:white; border-radius:4px;"
        )
        print_btn.setStyleSheet(
            "padding:6px; background:#4CAF50; color:white; border-radius:4px;"
        )
        save_btn.clicked.connect(self._save_bill_data)
        print_btn.clicked.connect(self._print_bill)
        act_row.addWidget(save_btn)
        act_row.addWidget(print_btn)
        form_layout.addLayout(act_row)
        form_layout.addStretch()

        form_widget.setLayout(form_layout)
        scroll.setWidget(form_widget)

        # ── Right: preview ──
        preview_widget = QWidget()
        preview_layout = QVBoxLayout()
        preview_layout.addWidget(QLabel("📄 Xem Trước Hóa Đơn:"))
        self.bill_preview = QTextEdit()
        self.bill_preview.setReadOnly(True)
        self.bill_preview.setFont(QFont("Courier New", 10))
        self.bill_preview.setStyleSheet("background:#f9f9f9; padding:8px;")
        preview_layout.addWidget(self.bill_preview)
        preview_widget.setLayout(preview_layout)

        splitter.addWidget(scroll)
        splitter.addWidget(preview_widget)
        splitter.setSizes([380, 520])
        layout.addWidget(splitter)
        return widget

    # ── Tab: Cài Đặt ──────────────────────────

    def _create_settings_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        grp = QGroupBox("💰 Giá Dịch Vụ Mặc Định")
        form = QFormLayout()

        self.set_elec_price = QDoubleSpinBox()
        self.set_elec_price.setMaximum(999_999)
        self.set_elec_price.setDecimals(0)
        self.set_elec_price.setSuffix(" đ/kWh")
        self.set_elec_price.setSingleStep(100)

        self.set_water_price = QDoubleSpinBox()
        self.set_water_price.setMaximum(999_999)
        self.set_water_price.setDecimals(0)
        self.set_water_price.setSuffix(" đ/khối")
        self.set_water_price.setSingleStep(1_000)

        self.set_laundry_price = QDoubleSpinBox()
        self.set_laundry_price.setMaximum(999_999)
        self.set_laundry_price.setDecimals(0)
        self.set_laundry_price.setSuffix(" đ/lần")
        self.set_laundry_price.setSingleStep(1_000)

        self.set_elec_price.setValue(self.db.get_setting('electricity_price') or 3500)
        self.set_water_price.setValue(self.db.get_setting('water_price') or 15000)
        self.set_laundry_price.setValue(self.db.get_setting('laundry_price') or 30000)

        form.addRow("Giá Điện:", self.set_elec_price)
        form.addRow("Giá Nước:", self.set_water_price)
        form.addRow("Giá Giặt:", self.set_laundry_price)

        save_btn = QPushButton("💾 Lưu Cài Đặt")
        save_btn.setStyleSheet(
            "padding:6px 12px; background:#2196F3; color:white; border-radius:4px;"
        )
        save_btn.clicked.connect(self._save_settings)
        form.addRow(save_btn)

        grp.setLayout(form)
        layout.addWidget(grp)
        layout.addStretch()
        return widget

    # ── Room Operations ───────────────────────

    def _load_rooms(self):
        """Tải danh sách phòng vào bảng và bill combo"""
        rooms = self.db.get_all_rooms()
        self.rooms_table.setRowCount(len(rooms))
        self.bill_room_combo.clear()

        for i, room in enumerate(rooms):
            start = room['start_date']
            start_disp = ''
            if start:
                try:
                    start_disp = datetime.strptime(start, '%Y-%m-%d').strftime('%d/%m/%Y')
                except ValueError:
                    start_disp = start

            status_disp = "Có người" if room['status'] == 'occupied' else "Trống"

            def _item(text):
                it = QTableWidgetItem(str(text))
                it.setTextAlignment(Qt.AlignCenter)
                return it

            self.rooms_table.setItem(i, 0, _item(room['name']))
            self.rooms_table.setItem(i, 1, _item(fmt_currency(room['price'])))
            self.rooms_table.setItem(i, 2, _item(start_disp))
            self.rooms_table.setItem(i, 3, _item(fmt_currency(room['deposit'])))

            status_item = _item(status_disp)
            if room['status'] == 'occupied':
                status_item.setBackground(QColor('#c8e6c9'))
            else:
                status_item.setBackground(QColor('#fff9c4'))
            self.rooms_table.setItem(i, 4, status_item)

            self.rooms_table.setItem(i, 5, _item(str(room['resident_count'])))
            self.rooms_table.item(i, 0).setData(Qt.UserRole, room['id'])

            self.bill_room_combo.addItem(room['name'], room['id'])

        self._update_dashboard()

    def _on_room_selected(self):
        row = self.rooms_table.currentRow()
        if row < 0:
            self.selected_room_id = None
            self.residents_table.setRowCount(0)
            return
        item = self.rooms_table.item(row, 0)
        if item:
            self.selected_room_id = item.data(Qt.UserRole)
            self._load_residents(self.selected_room_id)

    def _load_residents(self, room_id):
        residents = self.db.get_residents_by_room(room_id)
        self.residents_table.setRowCount(len(residents))
        for i, r in enumerate(residents):
            dob = r['date_of_birth']
            dob_disp = ''
            if dob:
                try:
                    dob_disp = datetime.strptime(dob, '%Y-%m-%d').strftime('%d/%m/%Y')
                except ValueError:
                    dob_disp = dob

            def _item(text):
                it = QTableWidgetItem(str(text) if text else '')
                return it

            self.residents_table.setItem(i, 0, _item(r['name']))
            self.residents_table.setItem(i, 1, _item(r['cccd']))
            self.residents_table.setItem(i, 2, _item(dob_disp))
            self.residents_table.setItem(i, 3, _item(r['hometown']))
            self.residents_table.setItem(i, 4, _item(r['phone']))
            self.residents_table.item(i, 0).setData(Qt.UserRole, r['id'])

    def _add_room(self):
        dlg = RoomDialog(self)
        if dlg.exec_() != QDialog.Accepted:
            return
        name, price, start_date, deposit, billing_day, notes = dlg.get_data()
        if not name:
            QMessageBox.warning(self, "Lỗi", "Tên phòng không được để trống!")
            return
        try:
            self.db.add_room(name, price, start_date, deposit, billing_day, notes)
            self._load_rooms()
            QMessageBox.information(self, "✅ Thành công", f"Đã thêm phòng {name}!")
        except Exception as e:
            QMessageBox.critical(self, "❌ Lỗi", str(e))

    def _edit_room(self):
        if not self.selected_room_id:
            QMessageBox.information(self, "Thông báo", "Vui lòng chọn phòng cần sửa!")
            return
        room = self.db.get_room_by_id(self.selected_room_id)
        dlg = RoomDialog(self, room)
        if dlg.exec_() != QDialog.Accepted:
            return
        name, price, start_date, deposit, billing_day, notes = dlg.get_data()
        if not name:
            QMessageBox.warning(self, "Lỗi", "Tên phòng không được để trống!")
            return
        try:
            self.db.update_room(
                self.selected_room_id, name, price, start_date, deposit, billing_day, notes
            )
            self._load_rooms()
            self._reselect_room(self.selected_room_id)
            QMessageBox.information(self, "✅ Thành công", "Đã cập nhật phòng!")
        except Exception as e:
            QMessageBox.critical(self, "❌ Lỗi", str(e))

    def _delete_room(self):
        if not self.selected_room_id:
            QMessageBox.information(self, "Thông báo", "Vui lòng chọn phòng cần xóa!")
            return
        room = self.db.get_room_by_id(self.selected_room_id)
        reply = QMessageBox.question(
            self, "Xác nhận xóa",
            f"Bạn có chắc muốn xóa phòng {room['name']}?\n"
            "(Tất cả khách trọ và dữ liệu của phòng này cũng sẽ bị xóa)",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.db.delete_room(self.selected_room_id)
            self.selected_room_id = None
            self.residents_table.setRowCount(0)
            self._load_rooms()
            QMessageBox.information(self, "✅ Thành công", "Đã xóa phòng!")

    def _reselect_room(self, room_id):
        for row in range(self.rooms_table.rowCount()):
            item = self.rooms_table.item(row, 0)
            if item and item.data(Qt.UserRole) == room_id:
                self.rooms_table.selectRow(row)
                break

    # ── Resident Operations ───────────────────

    def _add_resident(self):
        if not self.selected_room_id:
            QMessageBox.information(self, "Thông báo", "Vui lòng chọn phòng trước!")
            return
        dlg = ResidentDialog(self, self.selected_room_id)
        if dlg.exec_() != QDialog.Accepted:
            return
        name, cccd, dob, hometown, phone = dlg.get_data()
        if not name:
            QMessageBox.warning(self, "Lỗi", "Tên khách trọ không được để trống!")
            return
        try:
            self.db.add_resident(self.selected_room_id, name, cccd, dob, hometown, phone)
            self._load_residents(self.selected_room_id)
            self._load_rooms()
            self._reselect_room(self.selected_room_id)
            QMessageBox.information(self, "✅ Thành công", f"Đã thêm khách trọ {name}!")
        except Exception as e:
            QMessageBox.critical(self, "❌ Lỗi", str(e))

    def _edit_resident(self):
        row = self.residents_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Thông báo", "Vui lòng chọn khách trọ cần sửa!")
            return
        item = self.residents_table.item(row, 0)
        if not item:
            return
        resident_id = item.data(Qt.UserRole)
        resident = self.db.get_resident_by_id(resident_id)
        if not resident:
            return

        dlg = ResidentDialog(self, self.selected_room_id, resident)
        if dlg.exec_() != QDialog.Accepted:
            return
        name, cccd, dob, hometown, phone = dlg.get_data()
        if not name:
            QMessageBox.warning(self, "Lỗi", "Tên khách trọ không được để trống!")
            return
        try:
            self.db.update_resident(resident_id, name, cccd, dob, hometown, phone)
            self._load_residents(self.selected_room_id)
            QMessageBox.information(self, "✅ Thành công", "Đã cập nhật thông tin khách trọ!")
        except Exception as e:
            QMessageBox.critical(self, "❌ Lỗi", str(e))

    def _delete_resident(self):
        row = self.residents_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Thông báo", "Vui lòng chọn khách trọ cần xóa!")
            return
        item = self.residents_table.item(row, 0)
        if not item:
            return
        resident_id = item.data(Qt.UserRole)
        name = item.text()
        reply = QMessageBox.question(
            self, "Xác nhận xóa",
            f"Bạn có chắc muốn xóa khách trọ {name}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.db.delete_resident(resident_id)
            self._load_residents(self.selected_room_id)
            self._load_rooms()
            self._reselect_room(self.selected_room_id)

    # ── Bill Operations ───────────────────────

    def _get_bill_month(self):
        """Trả về tháng dạng YYYY-MM từ input, hoặc None nếu không hợp lệ"""
        text = self.bill_month_input.text().strip()
        try:
            dt = datetime.strptime(text, '%m/%Y')
            return dt.strftime('%Y-%m')
        except ValueError:
            return None

    def _load_bill_data(self):
        room_id = self.bill_room_combo.currentData()
        month = self._get_bill_month()
        if not room_id or not month:
            QMessageBox.warning(
                self, "Lỗi",
                "Vui lòng chọn phòng và nhập tháng/năm hợp lệ (MM/YYYY)!"
            )
            return

        elec = self.db.get_electricity_reading(room_id, month)
        self.elec_old.setValue(elec['old_reading'] if elec else 0)
        self.elec_new.setValue(elec['new_reading'] if elec else 0)

        water = self.db.get_water_reading(room_id, month)
        self.water_old.setValue(water['old_reading'] if water else 0)
        self.water_new.setValue(water['new_reading'] if water else 0)

        laundry = self.db.get_laundry_record(room_id, month)
        self.laundry_times.setValue(laundry['times'] if laundry else 0)
        self.laundry_amount.setValue(laundry['amount'] if laundry else 0)

        expense = self.db.get_monthly_expense(room_id, month)
        self.other_amount.setValue(expense['amount'] if expense else 0)
        self.other_notes.setText(expense['notes'] if (expense and expense['notes']) else '')

        self._update_preview()

    def _on_laundry_times_changed(self, times):
        if times > 0:
            price = self.db.get_setting('laundry_price') or 30000
            # Temporarily block signal to avoid recursion
            self.laundry_amount.blockSignals(True)
            self.laundry_amount.setValue(times * price)
            self.laundry_amount.blockSignals(False)
        self._update_preview()

    def _update_preview(self):
        room_id = self.bill_room_combo.currentData()
        month = self._get_bill_month()

        if not room_id or not month:
            self.bill_preview.setPlainText("(Chọn phòng và tháng để xem hóa đơn)")
            return

        room = self.db.get_room_by_id(room_id)
        if not room:
            return

        elec_price = self.db.get_setting('electricity_price') or 3500
        water_price = self.db.get_setting('water_price') or 15000
        laundry_price = self.db.get_setting('laundry_price') or 30000

        room_fee = room['price'] or 0

        elec_usage = max(0, self.elec_new.value() - self.elec_old.value())
        elec_fee = elec_usage * elec_price

        water_usage = max(0, self.water_new.value() - self.water_old.value())
        water_fee = water_usage * water_price

        laundry_fee = self.laundry_amount.value()
        laundry_times = self.laundry_times.value()

        other_fee = self.other_amount.value()
        other_notes = self.other_notes.text().strip()

        total = room_fee + elec_fee + water_fee + laundry_fee + other_fee

        # Update inline labels
        self.elec_usage_lbl.setText(f"{int(elec_usage)} kWh")
        self.elec_fee_lbl.setText(fmt_currency(elec_fee))
        self.water_usage_lbl.setText(f"{int(water_usage)} khối")
        self.water_fee_lbl.setText(fmt_currency(water_fee))

        try:
            dt = datetime.strptime(month, '%Y-%m')
            month_disp = dt.strftime('%m/%Y')
        except ValueError:
            month_disp = month

        lines = [
            "━" * 32,
            "    HÓA ĐƠN TIỀN PHÒNG",
            "━" * 32,
            "",
            f"Phòng: {room['name']}",
            f"Tháng: {month_disp}",
            "",
            "━━━ CHI TIẾT ━━━",
            f"Tiền Phòng:   {fmt_currency(room_fee)}",
        ]

        if self.elec_old.value() > 0 or self.elec_new.value() > 0:
            lines.append(f"Tiền Điện:    {fmt_currency(elec_fee)}")
            lines.append(
                f"  ({int(self.elec_old.value())}→{int(self.elec_new.value())} "
                f"= {int(elec_usage)} kWh × {fmt_currency(elec_price)})"
            )

        if self.water_old.value() > 0 or self.water_new.value() > 0:
            lines.append(f"Tiền Nước:    {fmt_currency(water_fee)}")
            lines.append(
                f"  ({int(self.water_old.value())}→{int(self.water_new.value())} "
                f"= {int(water_usage)} khối × {fmt_currency(water_price)})"
            )

        if laundry_fee > 0:
            lines.append(f"Tiền Giặt:    {fmt_currency(laundry_fee)}")
            if laundry_times > 0:
                lines.append(
                    f"  ({laundry_times} lần × {fmt_currency(laundry_price)})"
                )

        if other_fee > 0:
            lines.append(f"Chi Phí Khác: {fmt_currency(other_fee)}")
            if other_notes:
                lines.append(f"  (Ghi chú: {other_notes})")

        lines += [
            "",
            "━━━ TỔNG ━━━",
            f"TỔNG HÓA ĐƠN: {fmt_currency(total)}",
            "",
            "━" * 32,
        ]
        self.bill_preview.setPlainText('\n'.join(lines))

    def _save_bill_data(self):
        room_id = self.bill_room_combo.currentData()
        month = self._get_bill_month()
        if not room_id or not month:
            QMessageBox.warning(
                self, "Lỗi",
                "Vui lòng chọn phòng và nhập tháng/năm hợp lệ (MM/YYYY)!"
            )
            return
        try:
            self.db.save_electricity_reading(
                room_id, month, self.elec_old.value(), self.elec_new.value()
            )
            self.db.save_water_reading(
                room_id, month, self.water_old.value(), self.water_new.value()
            )
            self.db.save_laundry_record(
                room_id, month, self.laundry_times.value(), self.laundry_amount.value()
            )
            self.db.save_monthly_expense(
                room_id, month, self.other_amount.value(), self.other_notes.text().strip()
            )
            QMessageBox.information(self, "✅ Thành công", "Đã lưu dữ liệu tháng!")
        except Exception as e:
            QMessageBox.critical(self, "❌ Lỗi", str(e))

    def _print_bill(self):
        """Lưu dữ liệu và hiện hóa đơn trong dialog"""
        self._save_bill_data()

        bill_text = self.bill_preview.toPlainText().strip()
        if not bill_text:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("🖨️ Hóa Đơn")
        dlg.setMinimumWidth(420)
        layout = QVBoxLayout()

        te = QTextEdit()
        te.setReadOnly(True)
        te.setPlainText(bill_text)
        te.setFont(QFont("Courier New", 11))
        layout.addWidget(te)

        btn_row = QHBoxLayout()
        copy_btn = QPushButton("📋 Copy")
        close_btn = QPushButton("❌ Đóng")
        copy_btn.clicked.connect(
            lambda: QApplication.clipboard().setText(bill_text)
        )
        close_btn.clicked.connect(dlg.close)
        btn_row.addWidget(copy_btn)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        dlg.setLayout(layout)
        dlg.exec_()

    # ── Settings ─────────────────────────────

    def _save_settings(self):
        try:
            self.db.update_setting('electricity_price', self.set_elec_price.value())
            self.db.update_setting('water_price', self.set_water_price.value())
            self.db.update_setting('laundry_price', self.set_laundry_price.value())
            QMessageBox.information(self, "✅ Thành công", "Đã lưu cài đặt giá!")
        except Exception as e:
            QMessageBox.critical(self, "❌ Lỗi", str(e))

    # ── Export Excel ──────────────────────────

    def _export_excel(self):
        """Xuất danh sách khách trọ ra file Excel"""
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Danh Sách Khách Trọ"

            headers = ["Phòng", "Tên", "CCCD", "Ngày Sinh", "Quê Quán", "SĐT"]
            ws.append(headers)

            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill("solid", fgColor="4472C4")
            center = Alignment(horizontal='center')
            for cell in ws[1]:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center

            residents = self.db.get_all_residents()
            for r in residents:
                dob = r['date_of_birth']
                if dob:
                    try:
                        dob = datetime.strptime(dob, '%Y-%m-%d').strftime('%d/%m/%Y')
                    except ValueError:
                        pass
                ws.append([
                    r['room_name'],
                    r['name'],
                    r['cccd'] or '',
                    dob or '',
                    r['hometown'] or '',
                    r['phone'] or '',
                ])

            # Auto-fit column widths
            for col in ws.columns:
                max_len = max(
                    (len(str(cell.value)) for cell in col if cell.value is not None), default=10
                )
                ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)

            today = datetime.now().strftime('%Y-%m-%d')
            default_name = f"DanhSachKhachTro_{today}.xlsx"

            path, _ = QFileDialog.getSaveFileName(
                self, "Lưu File Excel", default_name,
                "Excel Files (*.xlsx)"
            )
            if not path:
                return
            if not path.endswith('.xlsx'):
                path += '.xlsx'
            wb.save(path)
            QMessageBox.information(self, "✅ Xuất Excel", f"Đã lưu file:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "❌ Lỗi xuất Excel", str(e))

    # ── Notifications ─────────────────────────

    def _check_billing_notifications(self):
        """Kiểm tra và thông báo ngày tính tiền cho các phòng đang có người khi khởi động"""
        today = datetime.now().day
        rooms = self.db.get_all_rooms()
        due = [
            room['name']
            for room in rooms
            if room['status'] == 'occupied' and room['billing_day'] == today
        ]
        if due:
            room_list = '\n'.join(f"• Phòng {name}" for name in due)
            QMessageBox.information(
                self,
                "🔔 Nhắc Nhở Thu Tiền",
                f"Hôm nay là ngày tính tiền của:\n{room_list}\n\n"
                "Vui lòng thu tiền phòng!",
            )

    # ── Dashboard ─────────────────────────────

    def _update_dashboard(self):
        stats = self.db.get_statistics()
        self.lbl_total.setText(f"Tổng phòng: {stats['total_rooms']}")
        self.lbl_occupied.setText(f"Có người: {stats['occupied_rooms']}")
        self.lbl_guests.setText(f"Khách trọ: {stats['total_residents']}")


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    window = RoomManagementApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
