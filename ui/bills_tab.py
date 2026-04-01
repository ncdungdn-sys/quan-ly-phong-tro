"""
Tab Hóa Đơn - Tạo và quản lý hóa đơn hàng tháng.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSpinBox, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QMessageBox, QFileDialog, QFrame,
    QDoubleSpinBox, QFormLayout, QTextBrowser
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from database import db_manager
from utils.helpers import (
    format_currency, get_current_month_year,
    calculate_room_bill, generate_monthly_bills
)


class BillDetailDialog(QDialog):
    """Dialog xem chi tiết hóa đơn."""

    def __init__(self, parent=None, bill_data=None, residents=None):
        super().__init__(parent)
        self.bill_data = bill_data or {}
        self.residents = residents or []
        self.setWindowTitle(f"Chi Tiết Hóa Đơn - Phòng {bill_data.get('room_number', '')}")
        self.setMinimumWidth(500)
        self.setMinimumHeight(500)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Thông tin phòng
        info_label = QLabel(
            f"🏠 Phòng: <b>{self.bill_data.get('room_number', '')}</b> | "
            f"📅 Tháng: <b>{self.bill_data.get('month', 0):02d}/{self.bill_data.get('year', 0)}</b>"
        )
        info_label.setStyleSheet("font-size: 14px; padding: 8px; background: #e3f2fd; border-radius: 5px;")
        layout.addWidget(info_label)

        # Cư dân
        if self.residents:
            names = ", ".join(r.get("full_name", "") for r in self.residents)
            res_label = QLabel(f"👥 Cư dân: {names}")
            res_label.setStyleSheet("font-size: 12px; padding: 4px;")
            layout.addWidget(res_label)

        # Chi tiết
        detail_browser = QTextBrowser()
        detail_browser.setOpenExternalLinks(False)

        bd = self.bill_data
        html = f"""
        <style>
            table {{ width: 100%; border-collapse: collapse; }}
            td, th {{ padding: 8px; border-bottom: 1px solid #eee; }}
            th {{ background: #1976D2; color: white; text-align: left; }}
            tr:nth-child(even) {{ background: #f5f5f5; }}
            .amount {{ text-align: right; font-weight: bold; }}
            .total {{ background: #fff3e0 !important; font-size: 16px; }}
        </style>
        <table>
        <tr><th>Khoản</th><th>Chi tiết</th><th class="amount">Số tiền</th></tr>
        <tr><td>🏠 Tiền phòng</td><td></td><td class="amount">{format_currency(bd.get('rent_amount', 0))}</td></tr>
        <tr>
            <td>⚡ Tiền điện</td>
            <td>{bd.get('old_reading', 0):.0f} → {bd.get('new_reading', 0):.0f} ({bd.get('units_used', 0):.0f} số × {format_currency(float(db_manager.get_setting('electricity_price', '3500')))})</td>
            <td class="amount">{format_currency(bd.get('electricity_amount', 0))}</td>
        </tr>
        <tr>
            <td>💧 Tiền nước</td>
            <td>{bd.get('num_people', 0)} người × {format_currency(float(db_manager.get_setting('water_price_per_person', '50000')))}</td>
            <td class="amount">{format_currency(bd.get('water_amount', 0))}</td>
        </tr>
        <tr>
            <td>👕 Tiền giặt</td>
            <td>{bd.get('num_people', 0)} người</td>
            <td class="amount">{format_currency(bd.get('laundry_amount', 0))}</td>
        </tr>
        """

        if bd.get("garbage_amount", 0) > 0:
            html += f"<tr><td>🗑️ Tiền rác</td><td></td><td class='amount'>{format_currency(bd.get('garbage_amount', 0))}</td></tr>"
        if bd.get("internet_amount", 0) > 0:
            html += f"<tr><td>🌐 Tiền internet</td><td></td><td class='amount'>{format_currency(bd.get('internet_amount', 0))}</td></tr>"
        if bd.get("room_expense_amount", 0) > 0:
            html += f"<tr><td>🔧 Chi phí phòng</td><td></td><td class='amount'>{format_currency(bd.get('room_expense_amount', 0))}</td></tr>"
        if bd.get("other_amount", 0) > 0:
            html += f"<tr><td>📌 Khác</td><td></td><td class='amount'>{format_currency(bd.get('other_amount', 0))}</td></tr>"

        html += f"""
        <tr class="total"><td colspan="2"><b>💰 TỔNG CỘNG</b></td><td class="amount"><b>{format_currency(bd.get('total_amount', 0))}</b></td></tr>
        </table>
        """

        detail_browser.setHtml(html)
        layout.addWidget(detail_browser)

        # Trạng thái
        status = bd.get("status", "unpaid")
        paid = bd.get("paid_amount", 0)
        total = bd.get("total_amount", 0)
        status_text = {"paid": "✅ Đã thanh toán", "unpaid": "❌ Chưa thanh toán", "partial": "⚠️ Thanh toán một phần"}.get(status, "❌ Chưa thanh toán")
        status_label = QLabel(f"Trạng thái: {status_text} | Đã thu: {format_currency(paid)}")
        status_label.setStyleSheet("font-size: 12px; padding: 5px;")
        layout.addWidget(status_label)

        # Buttons
        btn_layout = QHBoxLayout()

        if status != "paid":
            pay_btn = QPushButton("💰 Đánh Dấu Đã Thu")
            pay_btn.setStyleSheet("background: #388E3C; color: white; border-radius: 5px; padding: 7px 14px;")
            pay_btn.clicked.connect(lambda: self._mark_paid(bd.get("id"), total))
            btn_layout.addWidget(pay_btn)

        print_btn = QPushButton("🖨️ In PDF")
        print_btn.setStyleSheet("background: #1976D2; color: white; border-radius: 5px; padding: 7px 14px;")
        print_btn.clicked.connect(self._print_pdf)
        btn_layout.addWidget(print_btn)

        thermal_btn = QPushButton("🖨️ In Nhiệt")
        thermal_btn.setStyleSheet("background: #7B1FA2; color: white; border-radius: 5px; padding: 7px 14px;")
        thermal_btn.clicked.connect(self._print_thermal)
        btn_layout.addWidget(thermal_btn)

        close_btn = QPushButton("❌ Đóng")
        close_btn.setStyleSheet("background: #9E9E9E; color: white; border-radius: 5px; padding: 7px 14px;")
        close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _mark_paid(self, bill_id, total):
        """Đánh dấu đã thanh toán."""
        if not bill_id:
            return
        try:
            db_manager.update_bill_payment(bill_id, total, "paid")
            db_manager.add_transaction(
                bill_id,
                self.bill_data.get("room_id"),
                total,
                "payment",
                f"Thu tiền tháng {self.bill_data.get('month')}/{self.bill_data.get('year')}"
            )
            QMessageBox.information(self, "Thành công", "Đã đánh dấu thanh toán!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể cập nhật: {e}")

    def _print_pdf(self):
        """In hóa đơn PDF A4."""
        try:
            from utils.pdf_generator import generate_bill_pdf
            output_path, _ = QFileDialog.getSaveFileName(
                self, "Lưu file PDF",
                f"HoaDon_{self.bill_data.get('room_number', 'P')}_{self.bill_data.get('month', 0):02d}_{self.bill_data.get('year', 0)}.pdf",
                "PDF files (*.pdf)"
            )
            if output_path:
                path = generate_bill_pdf(self.bill_data, self.residents, output_path)
                QMessageBox.information(self, "Thành công", f"Đã lưu PDF:\n{path}")
        except ImportError:
            QMessageBox.warning(self, "Lỗi", "Cần cài reportlab:\npip install reportlab")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể xuất PDF: {e}")

    def _print_thermal(self):
        """In hóa đơn nhiệt 80mm."""
        try:
            from utils.pdf_generator import generate_thermal_bill
            output_path, _ = QFileDialog.getSaveFileName(
                self, "Lưu file PDF nhiệt",
                f"Bill_Nhiet_{self.bill_data.get('room_number', 'P')}_{self.bill_data.get('month', 0):02d}_{self.bill_data.get('year', 0)}.pdf",
                "PDF files (*.pdf)"
            )
            if output_path:
                path = generate_thermal_bill(self.bill_data, self.residents, output_path)
                QMessageBox.information(self, "Thành công", f"Đã lưu bill nhiệt:\n{path}")
        except ImportError:
            QMessageBox.warning(self, "Lỗi", "Cần cài reportlab:\npip install reportlab")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể xuất: {e}")


class BillsTab(QWidget):
    """Tab hóa đơn hàng tháng."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Tiêu đề
        title = QLabel("📋 Hóa Đơn Hàng Tháng")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #1565C0;")
        layout.addWidget(title)

        # Chọn tháng/năm + nút tạo
        ctrl_layout = QHBoxLayout()
        ctrl_layout.addWidget(QLabel("Tháng:"))
        self.month_spin = QSpinBox()
        self.month_spin.setRange(1, 12)
        month, year = get_current_month_year()
        self.month_spin.setValue(month)
        self.month_spin.setFixedWidth(60)
        ctrl_layout.addWidget(self.month_spin)

        ctrl_layout.addWidget(QLabel("Năm:"))
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2020, 2050)
        self.year_spin.setValue(year)
        self.year_spin.setFixedWidth(80)
        ctrl_layout.addWidget(self.year_spin)

        load_btn = QPushButton("📋 Tải")
        load_btn.setStyleSheet("background: #1976D2; color: white; border-radius: 5px; padding: 6px 12px;")
        load_btn.clicked.connect(self.refresh_data)
        ctrl_layout.addWidget(load_btn)

        ctrl_layout.addStretch()

        generate_btn = QPushButton("⚙️ Tạo Hóa Đơn Tháng Này")
        generate_btn.setStyleSheet("""
            QPushButton {
                background: #F57C00; color: white;
                border-radius: 5px; padding: 7px 14px;
                font-weight: bold; font-size: 12px;
            }
            QPushButton:hover { background: #E65100; }
        """)
        generate_btn.clicked.connect(self._generate_bills)
        ctrl_layout.addWidget(generate_btn)

        layout.addLayout(ctrl_layout)

        # Bảng hóa đơn
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "Phòng", "Tiền Phòng", "Điện", "Nước", "Giặt",
            "Rác", "Internet", "Chi Phí P.", "Tổng",
            "Trạng Thái", "Thao Tác"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(10, QHeaderView.Fixed)
        self.table.setColumnWidth(10, 120)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 11px;
            }
            QHeaderView::section {
                background: #1976D2;
                color: white;
                padding: 7px;
                font-weight: bold;
                border: none;
            }
        """)
        layout.addWidget(self.table)

        # Tổng kết
        self.summary_label = QLabel()
        self.summary_label.setStyleSheet("""
            background: #e8f5e9;
            border: 1px solid #4CAF50;
            border-radius: 5px;
            padding: 8px;
            font-size: 12px;
        """)
        layout.addWidget(self.summary_label)

    def refresh_data(self):
        """Làm mới danh sách hóa đơn."""
        month = self.month_spin.value()
        year = self.year_spin.value()

        bills = db_manager.get_bills_by_month(month, year)

        self.table.setRowCount(0)
        total_revenue = 0
        total_paid = 0
        unpaid_count = 0

        for bill in bills:
            row = self.table.rowCount()
            self.table.insertRow(row)

            def make_item(text, align=Qt.AlignRight | Qt.AlignVCenter):
                item = QTableWidgetItem(text)
                item.setTextAlignment(align)
                return item

            self.table.setItem(row, 0, make_item(bill.get("room_number", ""), Qt.AlignCenter))
            self.table.setItem(row, 1, make_item(format_currency(bill.get("rent_amount", 0))))
            self.table.setItem(row, 2, make_item(format_currency(bill.get("electricity_amount", 0))))
            self.table.setItem(row, 3, make_item(format_currency(bill.get("water_amount", 0))))
            self.table.setItem(row, 4, make_item(format_currency(bill.get("laundry_amount", 0))))
            self.table.setItem(row, 5, make_item(format_currency(bill.get("garbage_amount", 0))))
            self.table.setItem(row, 6, make_item(format_currency(bill.get("internet_amount", 0))))
            self.table.setItem(row, 7, make_item(format_currency(bill.get("room_expense_amount", 0))))
            self.table.setItem(row, 8, make_item(format_currency(bill.get("total_amount", 0))))

            # Trạng thái
            status = bill.get("status", "unpaid")
            status_map = {
                "paid": ("✅ Đã thu", "#4CAF50"),
                "unpaid": ("❌ Chưa thu", "#D32F2F"),
                "partial": ("⚠️ Một phần", "#F57C00"),
            }
            status_text, status_color = status_map.get(status, ("❌ Chưa thu", "#D32F2F"))
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(QColor(status_color))
            self.table.setItem(row, 9, status_item)

            # Action buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(3, 2, 3, 2)
            action_layout.setSpacing(3)

            view_btn = QPushButton("🔍")
            view_btn.setToolTip("Xem chi tiết")
            view_btn.setFixedSize(30, 26)
            view_btn.setStyleSheet("background: #1976D2; color: white; border-radius: 3px;")
            view_btn.clicked.connect(lambda _, b=bill: self._view_bill(b))
            action_layout.addWidget(view_btn)

            if status != "paid":
                pay_btn = QPushButton("💰")
                pay_btn.setToolTip("Thu tiền")
                pay_btn.setFixedSize(30, 26)
                pay_btn.setStyleSheet("background: #388E3C; color: white; border-radius: 3px;")
                pay_btn.clicked.connect(lambda _, b=bill: self._quick_pay(b))
                action_layout.addWidget(pay_btn)

            self.table.setCellWidget(row, 10, action_widget)
            self.table.setRowHeight(row, 40)

            total_revenue += bill.get("total_amount", 0)
            if status == "paid":
                total_paid += bill.get("total_amount", 0)
            else:
                unpaid_count += 1

        self.summary_label.setText(
            f"📊 Tháng {month:02d}/{year} | "
            f"Tổng hóa đơn: {len(bills)} | "
            f"Tổng doanh thu: {format_currency(total_revenue)} | "
            f"Đã thu: {format_currency(total_paid)} | "
            f"Chưa thu: {unpaid_count} hóa đơn"
        )

    def _generate_bills(self):
        """Tạo hóa đơn cho tháng hiện tại."""
        month = self.month_spin.value()
        year = self.year_spin.value()
        reply = QMessageBox.question(
            self,
            "Xác nhận tạo hóa đơn",
            f"Tạo hóa đơn cho tháng {month:02d}/{year}?\n"
            "Hóa đơn đã tồn tại sẽ được cập nhật lại.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                bills = generate_monthly_bills(month, year)
                self.refresh_data()
                QMessageBox.information(
                    self, "Thành công",
                    f"Đã tạo/cập nhật {len(bills)} hóa đơn cho tháng {month:02d}/{year}!"
                )
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể tạo hóa đơn: {e}")

    def _view_bill(self, bill):
        """Xem chi tiết hóa đơn."""
        room_id = bill.get("room_id")
        month = bill.get("month")
        year = bill.get("year")

        # Tính lại bill_data đầy đủ
        bill_data = calculate_room_bill(room_id, month, year)
        if not bill_data:
            bill_data = bill

        # Thêm ID
        bill_data["id"] = bill.get("id")
        bill_data["status"] = bill.get("status", "unpaid")
        bill_data["paid_amount"] = bill.get("paid_amount", 0)

        residents = db_manager.get_residents_by_room(room_id, active_only=True)
        dialog = BillDetailDialog(self, bill_data=bill_data, residents=residents)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_data()

    def _quick_pay(self, bill):
        """Thu tiền nhanh."""
        total = bill.get("total_amount", 0)
        reply = QMessageBox.question(
            self,
            "Thu tiền",
            f"Thu tiền phòng {bill.get('room_number', '')}?\n"
            f"Số tiền: {format_currency(total)}",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                db_manager.update_bill_payment(bill["id"], total, "paid")
                db_manager.add_transaction(
                    bill["id"],
                    bill["room_id"],
                    total,
                    "payment",
                    f"Thu tiền tháng {bill.get('month')}/{bill.get('year')}"
                )
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể cập nhật: {e}")
