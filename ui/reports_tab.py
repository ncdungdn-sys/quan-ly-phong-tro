"""
Tab Báo Cáo - Xem thống kê doanh thu, chi phí, lợi nhuận.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSpinBox, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget, QFileDialog, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from database import db_manager
from utils.helpers import format_currency, get_current_month_year, get_month_name


class ReportsTab(QWidget):
    """Tab báo cáo thống kê."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Tiêu đề
        title = QLabel("📊 Báo Cáo & Thống Kê")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #1565C0;")
        layout.addWidget(title)

        # Sub-tabs
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

        # Tab báo cáo tháng
        monthly_tab = QWidget()
        self._setup_monthly_tab(monthly_tab)
        self.sub_tabs.addTab(monthly_tab, "📅 Theo Tháng")

        # Tab báo cáo năm
        yearly_tab = QWidget()
        self._setup_yearly_tab(yearly_tab)
        self.sub_tabs.addTab(yearly_tab, "📆 Theo Năm")

        # Tab giao dịch
        trans_tab = QWidget()
        self._setup_transactions_tab(trans_tab)
        self.sub_tabs.addTab(trans_tab, "💳 Giao Dịch")

        layout.addWidget(self.sub_tabs)

    def _setup_monthly_tab(self, parent):
        """Tab báo cáo tháng."""
        layout = QVBoxLayout(parent)

        ctrl_layout = QHBoxLayout()
        ctrl_layout.addWidget(QLabel("Tháng:"))
        self.monthly_month = QSpinBox()
        self.monthly_month.setRange(1, 12)
        month, year = get_current_month_year()
        self.monthly_month.setValue(month)
        self.monthly_month.setFixedWidth(60)
        ctrl_layout.addWidget(self.monthly_month)

        ctrl_layout.addWidget(QLabel("Năm:"))
        self.monthly_year = QSpinBox()
        self.monthly_year.setRange(2020, 2050)
        self.monthly_year.setValue(year)
        self.monthly_year.setFixedWidth(80)
        ctrl_layout.addWidget(self.monthly_year)

        load_btn = QPushButton("📊 Xem báo cáo")
        load_btn.setStyleSheet("background: #1976D2; color: white; border-radius: 5px; padding: 6px 12px;")
        load_btn.clicked.connect(self._load_monthly_report)
        ctrl_layout.addWidget(load_btn)

        ctrl_layout.addStretch()

        export_btn = QPushButton("📤 Xuất Excel")
        export_btn.setStyleSheet("background: #388E3C; color: white; border-radius: 5px; padding: 6px 12px;")
        export_btn.clicked.connect(self._export_monthly)
        ctrl_layout.addWidget(export_btn)

        layout.addLayout(ctrl_layout)

        # Summary cards
        cards_layout = QHBoxLayout()

        self.monthly_cards = {}
        card_configs = [
            ("revenue", "💵 Doanh Thu", "#1976D2"),
            ("paid", "✅ Đã Thu", "#388E3C"),
            ("expenses", "📤 Chi Phí", "#D32F2F"),
            ("profit", "📈 Lợi Nhuận", "#F57C00"),
        ]

        for key, title, color in card_configs:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: white;
                    border: 2px solid {color};
                    border-radius: 8px;
                    padding: 5px;
                }}
                QLabel {{ border: none; background: transparent; }}
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(3)

            t_label = QLabel(title)
            t_label.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: bold;")
            card_layout.addWidget(t_label)

            v_label = QLabel("0đ")
            v_label.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold;")
            card_layout.addWidget(v_label)

            self.monthly_cards[key] = v_label
            cards_layout.addWidget(card)

        layout.addLayout(cards_layout)

        # Bảng chi tiết hóa đơn tháng
        self.monthly_table = QTableWidget()
        self.monthly_table.setColumnCount(5)
        self.monthly_table.setHorizontalHeaderLabels([
            "Phòng", "Tổng", "Đã Thu", "Chưa Thu", "Trạng Thái"
        ])
        self.monthly_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.monthly_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.monthly_table.setAlternatingRowColors(True)
        self.monthly_table.setStyleSheet("""
            QTableWidget { border: 1px solid #ddd; border-radius: 5px; font-size: 12px; }
            QHeaderView::section {
                background: #1976D2; color: white;
                padding: 7px; font-weight: bold; border: none;
            }
        """)
        layout.addWidget(self.monthly_table)

    def _setup_yearly_tab(self, parent):
        """Tab báo cáo năm."""
        layout = QVBoxLayout(parent)

        ctrl_layout = QHBoxLayout()
        ctrl_layout.addWidget(QLabel("Năm:"))
        self.yearly_year = QSpinBox()
        self.yearly_year.setRange(2020, 2050)
        _, year = get_current_month_year()
        self.yearly_year.setValue(year)
        self.yearly_year.setFixedWidth(80)
        ctrl_layout.addWidget(self.yearly_year)

        load_btn = QPushButton("📊 Xem báo cáo năm")
        load_btn.setStyleSheet("background: #1976D2; color: white; border-radius: 5px; padding: 6px 12px;")
        load_btn.clicked.connect(self._load_yearly_report)
        ctrl_layout.addWidget(load_btn)

        ctrl_layout.addStretch()

        export_btn = QPushButton("📤 Xuất Excel")
        export_btn.setStyleSheet("background: #388E3C; color: white; border-radius: 5px; padding: 6px 12px;")
        export_btn.clicked.connect(self._export_yearly)
        ctrl_layout.addWidget(export_btn)

        layout.addLayout(ctrl_layout)

        self.yearly_table = QTableWidget()
        self.yearly_table.setColumnCount(5)
        self.yearly_table.setHorizontalHeaderLabels([
            "Tháng", "Doanh Thu", "Đã Thu", "Chi Phí", "Lợi Nhuận"
        ])
        self.yearly_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.yearly_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.yearly_table.setAlternatingRowColors(True)
        self.yearly_table.setStyleSheet("""
            QTableWidget { border: 1px solid #ddd; border-radius: 5px; font-size: 12px; }
            QHeaderView::section {
                background: #388E3C; color: white;
                padding: 7px; font-weight: bold; border: none;
            }
        """)
        layout.addWidget(self.yearly_table)

        self.yearly_total_label = QLabel()
        self.yearly_total_label.setStyleSheet("""
            background: #e8f5e9;
            border: 1px solid #4CAF50;
            border-radius: 5px;
            padding: 8px;
            font-size: 13px;
            font-weight: bold;
        """)
        layout.addWidget(self.yearly_total_label)

    def _setup_transactions_tab(self, parent):
        """Tab giao dịch."""
        layout = QVBoxLayout(parent)

        self.trans_table = QTableWidget()
        self.trans_table.setColumnCount(5)
        self.trans_table.setHorizontalHeaderLabels([
            "Phòng", "Loại", "Số Tiền", "Mô Tả", "Ngày"
        ])
        self.trans_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.trans_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.trans_table.setAlternatingRowColors(True)
        self.trans_table.setStyleSheet("""
            QTableWidget { border: 1px solid #ddd; border-radius: 5px; font-size: 12px; }
            QHeaderView::section {
                background: #7B1FA2; color: white;
                padding: 7px; font-weight: bold; border: none;
            }
        """)
        layout.addWidget(self.trans_table)

    def refresh_data(self):
        """Làm mới dữ liệu."""
        self._load_monthly_report()
        self._load_yearly_report()
        self._load_transactions()

    def _load_monthly_report(self):
        """Tải báo cáo tháng."""
        month = self.monthly_month.value()
        year = self.monthly_year.value()

        summary = db_manager.get_monthly_summary(month, year)
        self.monthly_cards["revenue"].setText(format_currency(summary["total_revenue"]))
        self.monthly_cards["paid"].setText(format_currency(summary["paid_revenue"]))
        self.monthly_cards["expenses"].setText(format_currency(summary["total_cost"]))
        profit = summary["profit"]
        self.monthly_cards["profit"].setText(format_currency(profit))
        if profit >= 0:
            self.monthly_cards["profit"].setStyleSheet("color: #388E3C; font-size: 16px; font-weight: bold; border: none;")
        else:
            self.monthly_cards["profit"].setStyleSheet("color: #D32F2F; font-size: 16px; font-weight: bold; border: none;")

        bills = db_manager.get_bills_by_month(month, year)
        self.monthly_table.setRowCount(0)
        for bill in bills:
            row = self.monthly_table.rowCount()
            self.monthly_table.insertRow(row)

            total = bill.get("total_amount", 0)
            paid = bill.get("paid_amount", 0)
            unpaid = total - paid

            self.monthly_table.setItem(row, 0, QTableWidgetItem(bill.get("room_number", "")))
            self.monthly_table.setItem(row, 1, QTableWidgetItem(format_currency(total)))
            self.monthly_table.setItem(row, 2, QTableWidgetItem(format_currency(paid)))
            self.monthly_table.setItem(row, 3, QTableWidgetItem(format_currency(unpaid)))

            status = bill.get("status", "unpaid")
            status_map = {"paid": "✅ Đã thu", "unpaid": "❌ Chưa thu", "partial": "⚠️ Một phần"}
            status_item = QTableWidgetItem(status_map.get(status, "❌ Chưa thu"))
            status_item.setTextAlignment(Qt.AlignCenter)
            self.monthly_table.setItem(row, 4, status_item)
            self.monthly_table.setRowHeight(row, 35)

    def _load_yearly_report(self):
        """Tải báo cáo năm."""
        year = self.yearly_year.value()
        summaries = db_manager.get_yearly_summary(year)

        self.yearly_table.setRowCount(0)
        total_revenue = total_paid = total_expenses = total_profit = 0

        for summary in summaries:
            if summary["total_revenue"] == 0 and summary["total_cost"] == 0:
                continue
            row = self.yearly_table.rowCount()
            self.yearly_table.insertRow(row)

            month = summary["month"]
            self.yearly_table.setItem(row, 0, QTableWidgetItem(f"Tháng {month:02d}/{year}"))
            self.yearly_table.setItem(row, 1, QTableWidgetItem(format_currency(summary["total_revenue"])))
            self.yearly_table.setItem(row, 2, QTableWidgetItem(format_currency(summary["paid_revenue"])))
            self.yearly_table.setItem(row, 3, QTableWidgetItem(format_currency(summary["total_cost"])))

            profit = summary["profit"]
            profit_item = QTableWidgetItem(format_currency(profit))
            profit_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if profit >= 0:
                profit_item.setForeground(QColor("#388E3C"))
            else:
                profit_item.setForeground(QColor("#D32F2F"))
            self.yearly_table.setItem(row, 4, profit_item)
            self.yearly_table.setRowHeight(row, 35)

            total_revenue += summary["total_revenue"]
            total_paid += summary["paid_revenue"]
            total_expenses += summary["total_cost"]
            total_profit += summary["profit"]

        self.yearly_total_label.setText(
            f"📊 Tổng năm {year} | "
            f"Doanh thu: {format_currency(total_revenue)} | "
            f"Đã thu: {format_currency(total_paid)} | "
            f"Chi phí: {format_currency(total_expenses)} | "
            f"Lợi nhuận: {format_currency(total_profit)}"
        )

    def _load_transactions(self):
        """Tải lịch sử giao dịch."""
        transactions = db_manager.get_transactions()
        self.trans_table.setRowCount(0)

        for trans in transactions[:100]:  # Giới hạn 100 giao dịch gần nhất
            row = self.trans_table.rowCount()
            self.trans_table.insertRow(row)

            self.trans_table.setItem(row, 0, QTableWidgetItem(trans.get("room_number", "")))

            type_map = {"payment": "💰 Thu tiền", "expense": "📤 Chi phí", "refund": "↩️ Hoàn tiền"}
            self.trans_table.setItem(row, 1, QTableWidgetItem(
                type_map.get(trans.get("transaction_type", ""), trans.get("transaction_type", ""))
            ))

            amount_item = QTableWidgetItem(format_currency(trans.get("amount", 0)))
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.trans_table.setItem(row, 2, amount_item)
            self.trans_table.setItem(row, 3, QTableWidgetItem(trans.get("description", "")))
            self.trans_table.setItem(row, 4, QTableWidgetItem(trans.get("transaction_date", "")))
            self.trans_table.setRowHeight(row, 35)

    def _export_monthly(self):
        """Xuất báo cáo tháng ra Excel."""
        try:
            from utils.excel_exporter import export_monthly_report
            month = self.monthly_month.value()
            year = self.monthly_year.value()
            output_path, _ = QFileDialog.getSaveFileName(
                self, "Lưu file Excel",
                f"BaoCao_T{month:02d}_{year}.xlsx",
                "Excel files (*.xlsx)"
            )
            if output_path:
                path = export_monthly_report(month, year, output_path)
                QMessageBox.information(self, "Thành công", f"Đã xuất:\n{path}")
        except ImportError:
            QMessageBox.warning(self, "Lỗi", "Cần cài pandas và openpyxl:\npip install pandas openpyxl")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể xuất: {e}")

    def _export_yearly(self):
        """Xuất báo cáo năm ra Excel."""
        try:
            from utils.excel_exporter import export_yearly_report
            year = self.yearly_year.value()
            output_path, _ = QFileDialog.getSaveFileName(
                self, "Lưu file Excel",
                f"BaoCao_Nam_{year}.xlsx",
                "Excel files (*.xlsx)"
            )
            if output_path:
                path = export_yearly_report(year, output_path)
                QMessageBox.information(self, "Thành công", f"Đã xuất:\n{path}")
        except ImportError:
            QMessageBox.warning(self, "Lỗi", "Cần cài pandas và openpyxl:\npip install pandas openpyxl")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể xuất: {e}")
