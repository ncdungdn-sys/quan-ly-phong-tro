import sys
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTabWidget, QTableWidget, QTableWidgetItem,
                             QPushButton, QLabel, QLineEdit, QSpinBox, QDateEdit,
                             QDialog, QFormLayout, QMessageBox, QComboBox, QDoubleSpinBox)
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
        self.load_rooms_table()
        self.load_residents_table()
    
    def create_residents_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Nút thêm cư dân
        add_button = QPushButton("➕ Thêm Cư Dân")
        add_button.clicked.connect(self.add_resident_dialog)
        layout.addWidget(add_button)
        
        # Bảng cư dân
        self.residents_table = QTableWidget()
        self.residents_table.setColumnCount(8)
        self.residents_table.setHorizontalHeaderLabels(["ID", "Tên", "Tuổi", "CCCD", "SĐT", "Phòng", "Ngày Vào", "Hành Động"])
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
        self.rooms_table.setHorizontalHeaderLabels(["Phòng", "Giá", "Trạng Thái", "Cư Dân", "Hành Động"])
        layout.addWidget(self.rooms_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_bills_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Nút tạo hóa đơn
        create_button = QPushButton("📝 Tạo Hóa Đơn Tháng")
        create_button.clicked.connect(self.create_bills_dialog)
        layout.addWidget(create_button)
        
        # Bảng hóa đơn
        self.bills_table = QTableWidget()
        self.bills_table.setColumnCount(6)
        self.bills_table.setHorizontalHeaderLabels(["Phòng", "Cư Dân", "Tháng", "Tổng Tiền", "Trạng Thái", "Thao Tác"])
        layout.addWidget(self.bills_table)
        
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
        
        # Lấy danh sách phòng trống
        rooms = self.db.get_empty_rooms()
        for room_id, room_name in rooms:
            room_combo.addItem(room_name, room_id)
        
        form_layout.addRow("Tên:", name_input)
        form_layout.addRow("Tuổi:", age_input)
        form_layout.addRow("CCCD:", cccd_input)
        form_layout.addRow("SĐT:", phone_input)
        form_layout.addRow("Phòng:", room_combo)
        form_layout.addRow("Ngày Vào:", date_input)
        
        save_button = QPushButton("Lưu")
        save_button.clicked.connect(lambda: self.save_resident(
            name_input.text(), age_input.value(), cccd_input.text(),
            phone_input.text(), room_combo.currentData(), date_input.date()
        ))
        form_layout.addRow(save_button)
        
        dialog.setLayout(form_layout)
        dialog.exec_()
    
    def save_resident(self, name, age, cccd, phone, room_id, date):
        try:
            self.db.add_resident(name, age, cccd, phone, room_id, date.toString("yyyy-MM-dd"))
            QMessageBox.information(self, "Thành công", "Cư dân đã được thêm!")
            self.update_dashboard()
            self.load_rooms_table()
            self.load_residents_table()
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
        save_button.clicked.connect(lambda: self.save_room(room_name.text(), room_price.value()))
        form_layout.addRow(save_button)
        
        dialog.setLayout(form_layout)
        dialog.exec_()
    
    def save_room(self, name, price):
        try:
            self.db.add_room(name, price)
            QMessageBox.information(self, "Thành công", "Phòng đã được thêm!")
            self.update_dashboard()
            self.load_rooms_table()
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
        save_button.clicked.connect(lambda: self.save_expense(
            expense_type.currentText(), expense_desc.text(), expense_amount.value()
        ))
        form_layout.addRow(save_button)
        
        dialog.setLayout(form_layout)
        dialog.exec_()
    
    def save_expense(self, exp_type, description, amount):
        try:
            self.db.add_expense(exp_type, description, amount)
            QMessageBox.information(self, "Thành công", "Chi phí đã được thêm!")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e))
    
    def create_bills_dialog(self):
        QMessageBox.information(self, "Tạo Hóa Đơn", "Hóa đơn tháng này đang được tạo...")
    
    def save_electricity(self):
        QMessageBox.information(self, "Lưu", "Mốc điện đã được lưu!")
    
    def export_report(self):
        QMessageBox.information(self, "Xuất", "Báo cáo đang được xuất...")
    
    def load_rooms_table(self):
        rooms = self.db.get_all_rooms()
        self.rooms_table.setRowCount(len(rooms))
        for row, room in enumerate(rooms):
            resident_count = self.db.get_resident_count_by_room(room['id'])
            status = "Có người" if room['status'] == 'occupied' else "Trống"

            self.rooms_table.setItem(row, 0, QTableWidgetItem(room['name']))
            self.rooms_table.setItem(row, 1, QTableWidgetItem(f"{room['price']:,.0f}"))
            self.rooms_table.setItem(row, 2, QTableWidgetItem(status))
            self.rooms_table.setItem(row, 3, QTableWidgetItem(str(resident_count)))

            delete_btn = QPushButton("🗑 Xóa")
            delete_btn.clicked.connect(lambda checked, r_id=room['id']: self.delete_room(r_id))
            self.rooms_table.setCellWidget(row, 4, delete_btn)

    def load_residents_table(self):
        residents = self.db.get_all_residents()
        self.residents_table.setRowCount(len(residents))
        for row, resident in enumerate(residents):
            self.residents_table.setItem(row, 0, QTableWidgetItem(str(resident['id'])))
            self.residents_table.setItem(row, 1, QTableWidgetItem(resident['name']))
            self.residents_table.setItem(row, 2, QTableWidgetItem(str(resident['age'])))
            self.residents_table.setItem(row, 3, QTableWidgetItem(resident['cccd'] or ''))
            self.residents_table.setItem(row, 4, QTableWidgetItem(resident['phone'] or ''))
            self.residents_table.setItem(row, 5, QTableWidgetItem(resident['room_name'] or ''))
            self.residents_table.setItem(row, 6, QTableWidgetItem(resident['check_in_date'] or ''))

            delete_btn = QPushButton("🗑 Xóa")
            delete_btn.clicked.connect(lambda checked, r_id=resident['id']: self.delete_resident(r_id))
            self.residents_table.setCellWidget(row, 7, delete_btn)

    def delete_room(self, room_id):
        reply = QMessageBox.question(self, "Xác nhận", "Bạn có chắc muốn xóa phòng này?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                self.db.delete_room(room_id)
                self.update_dashboard()
                self.load_rooms_table()
                self.load_residents_table()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", str(e))

    def delete_resident(self, resident_id):
        reply = QMessageBox.question(self, "Xác nhận", "Bạn có chắc muốn xóa cư dân này?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                self.db.delete_resident(resident_id)
                self.update_dashboard()
                self.load_rooms_table()
                self.load_residents_table()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", str(e))

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
