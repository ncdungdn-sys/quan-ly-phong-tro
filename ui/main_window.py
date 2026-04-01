"""
Cửa sổ chính của ứng dụng Quản Lý Phòng Trọ.
Chứa menu điều hướng và các tab chức năng.
"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QStatusBar, QMenuBar, QMenu, QAction,
    QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QFont

from ui.dashboard import DashboardWidget
from ui.residents_tab import ResidentsTab
from ui.electricity_tab import ElectricityTab
from ui.laundry_tab import LaundryTab
from ui.expenses_tab import ExpensesTab
from ui.bills_tab import BillsTab
from ui.reports_tab import ReportsTab
from ui.settings_tab import SettingsTab
from utils.helpers import get_current_month_year, format_currency
from datetime import datetime
from database import db_manager


class MainWindow(QMainWindow):
    """Cửa sổ chính của ứng dụng."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("🏠 Quản Lý Phòng Trọ")
        self.setMinimumSize(1100, 700)
        self.resize(1200, 800)

        self._setup_ui()
        self._setup_menu()
        self._setup_statusbar()
        self._setup_refresh_timer()

    def _setup_ui(self):
        """Thiết lập giao diện chính."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = self._create_header()
        main_layout.addWidget(header)

        # Tab widget chính
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setMovable(False)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: #f5f5f5;
            }
            QTabBar::tab {
                background: #e0e0e0;
                color: #333;
                padding: 8px 16px;
                margin-right: 2px;
                border-radius: 4px 4px 0 0;
                font-size: 13px;
                min-width: 80px;
            }
            QTabBar::tab:selected {
                background: #1976D2;
                color: white;
                font-weight: bold;
            }
            QTabBar::tab:hover:!selected {
                background: #bbdefb;
            }
        """)

        # Tạo các tab
        self.dashboard_tab = DashboardWidget()
        self.residents_tab = ResidentsTab()
        self.electricity_tab = ElectricityTab()
        self.laundry_tab = LaundryTab()
        self.expenses_tab = ExpensesTab()
        self.bills_tab = BillsTab()
        self.reports_tab = ReportsTab()
        self.settings_tab = SettingsTab()

        self.tab_widget.addTab(self.dashboard_tab, "🏠 Dashboard")
        self.tab_widget.addTab(self.residents_tab, "👥 Cư Dân")
        self.tab_widget.addTab(self.electricity_tab, "⚡ Điện")
        self.tab_widget.addTab(self.laundry_tab, "👕 Giặt")
        self.tab_widget.addTab(self.expenses_tab, "💰 Chi Phí")
        self.tab_widget.addTab(self.bills_tab, "📋 Hóa Đơn")
        self.tab_widget.addTab(self.reports_tab, "📊 Báo Cáo")
        self.tab_widget.addTab(self.settings_tab, "⚙️ Cài Đặt")

        # Kết nối sự kiện tab thay đổi
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        main_layout.addWidget(self.tab_widget)

    def _create_header(self):
        """Tạo thanh header."""
        header = QWidget()
        header.setFixedHeight(55)
        header.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #1565C0, stop: 1 #1976D2
                );
            }
        """)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(15, 0, 15, 0)

        title_label = QLabel("🏠 QUẢN LÝ PHÒNG TRỌ")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: white;")
        layout.addWidget(title_label)

        layout.addStretch()

        month, year = get_current_month_year()
        self.date_label = QLabel(f"Tháng {month:02d}/{year}")
        self.date_label.setStyleSheet("color: #bbdefb; font-size: 13px;")
        layout.addWidget(self.date_label)

        return header

    def _setup_menu(self):
        """Thiết lập menu bar."""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background: #1976D2;
                color: white;
                font-size: 12px;
            }
            QMenuBar::item:selected {
                background: #1565C0;
            }
            QMenu {
                background: white;
                color: black;
                border: 1px solid #ccc;
            }
            QMenu::item:selected {
                background: #bbdefb;
            }
        """)

        # Menu Tệp
        file_menu = menubar.addMenu("📁 Tệp")

        backup_action = QAction("💾 Backup dữ liệu", self)
        backup_action.triggered.connect(self._backup_database)
        file_menu.addAction(backup_action)

        restore_action = QAction("📂 Khôi phục dữ liệu", self)
        restore_action.triggered.connect(self._restore_database)
        file_menu.addAction(restore_action)

        file_menu.addSeparator()

        exit_action = QAction("❌ Thoát", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Menu Xuất
        export_menu = menubar.addMenu("📤 Xuất")

        export_excel_action = QAction("📊 Xuất Excel tháng này", self)
        export_excel_action.triggered.connect(self._export_monthly_excel)
        export_menu.addAction(export_excel_action)

        export_residents_action = QAction("👥 Xuất danh sách cư dân", self)
        export_residents_action.triggered.connect(self._export_residents)
        export_menu.addAction(export_residents_action)

        # Menu Trợ giúp
        help_menu = menubar.addMenu("❓ Trợ Giúp")

        about_action = QAction("ℹ️ Về ứng dụng", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_statusbar(self):
        """Thiết lập thanh trạng thái."""
        self.statusBar().showMessage("✅ Sẵn sàng")
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background: #e3f2fd;
                color: #1565C0;
                font-size: 12px;
                border-top: 1px solid #bbdefb;
            }
        """)

    def _setup_refresh_timer(self):
        """Thiết lập timer tự động làm mới dashboard."""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._auto_refresh)
        self.refresh_timer.start(60000)  # Làm mới mỗi 1 phút

    def _on_tab_changed(self, index):
        """Xử lý khi chuyển tab - làm mới dữ liệu."""
        tab = self.tab_widget.widget(index)
        if hasattr(tab, "refresh_data"):
            tab.refresh_data()

    def _auto_refresh(self):
        """Tự động làm mới dashboard."""
        if self.tab_widget.currentIndex() == 0:
            self.dashboard_tab.refresh_data()

    def _backup_database(self):
        """Sao lưu database."""
        import shutil
        from database.db_manager import DB_PATH
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Lưu backup",
            f"phong_tro_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
            "Database files (*.db)"
        )
        if output_path:
            try:
                shutil.copy2(DB_PATH, output_path)
                QMessageBox.information(self, "Thành công", f"Đã backup database vào:\n{output_path}")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể backup: {e}")

    def _restore_database(self):
        """Khôi phục database từ backup."""
        input_path, _ = QFileDialog.getOpenFileName(
            self, "Chọn file backup",
            "", "Database files (*.db)"
        )
        if input_path:
            reply = QMessageBox.warning(
                self, "Xác nhận",
                "Khôi phục sẽ ghi đè dữ liệu hiện tại. Bạn có chắc không?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                import shutil
                from database.db_manager import DB_PATH
                try:
                    shutil.copy2(input_path, DB_PATH)
                    QMessageBox.information(
                        self, "Thành công",
                        "Đã khôi phục database. Vui lòng khởi động lại ứng dụng!"
                    )
                except Exception as e:
                    QMessageBox.critical(self, "Lỗi", f"Không thể khôi phục: {e}")

    def _export_monthly_excel(self):
        """Xuất báo cáo tháng ra Excel."""
        try:
            from utils.excel_exporter import export_monthly_report
            month, year = get_current_month_year()
            output_path, _ = QFileDialog.getSaveFileName(
                self, "Lưu file Excel",
                f"BaoCao_T{month:02d}_{year}.xlsx",
                "Excel files (*.xlsx)"
            )
            if output_path:
                path = export_monthly_report(month, year, output_path)
                QMessageBox.information(self, "Thành công", f"Đã xuất báo cáo:\n{path}")
        except ImportError:
            QMessageBox.warning(self, "Lỗi", "Cần cài pandas và openpyxl:\npip install pandas openpyxl")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể xuất: {e}")

    def _export_residents(self):
        """Xuất danh sách cư dân ra Excel."""
        try:
            from utils.excel_exporter import export_residents_report
            output_path, _ = QFileDialog.getSaveFileName(
                self, "Lưu file Excel",
                "DanhSachCuDan.xlsx",
                "Excel files (*.xlsx)"
            )
            if output_path:
                path = export_residents_report(output_path)
                QMessageBox.information(self, "Thành công", f"Đã xuất danh sách:\n{path}")
        except ImportError:
            QMessageBox.warning(self, "Lỗi", "Cần cài pandas và openpyxl:\npip install pandas openpyxl")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể xuất: {e}")

    def _show_about(self):
        """Hiển thị thông tin về ứng dụng."""
        QMessageBox.about(
            self,
            "Về ứng dụng",
            "🏠 <b>Quản Lý Phòng Trọ</b><br><br>"
            "Phiên bản: 1.0.0<br>"
            "Ngôn ngữ: Python + PyQt5<br>"
            "Database: SQLite<br><br>"
            "Tính năng:<br>"
            "• Quản lý 7 phòng trọ<br>"
            "• Tính tiền điện, nước, giặt<br>"
            "• Hóa đơn và báo cáo<br>"
            "• In PDF hóa đơn<br>"
            "• Xuất Excel"
        )

    def closeEvent(self, event):
        """Xác nhận trước khi thoát."""
        reply = QMessageBox.question(
            self, "Xác nhận thoát",
            "Bạn có muốn thoát ứng dụng không?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
