import sqlite3
from datetime import datetime, timedelta
import os

class Database:
    def __init__(self, db_name="room_management.db"):
        self.db_name = db_name
        self.conn = None
        self.init_database()
    
    def init_database(self):
        """Khởi tạo database và các bảng"""
        self.conn = sqlite3.connect(self.db_name)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        
        # Bảng Rooms (Phòng)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                status TEXT DEFAULT 'empty',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Bảng Residents (Cư dân)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS residents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER,
                cccd TEXT UNIQUE,
                phone TEXT,
                room_id INTEGER NOT NULL,
                check_in_date DATE NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (room_id) REFERENCES rooms(id)
            )
        ''')
        
        # Bảng ElectricityMeter (Mốc điện)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS electricity_meter (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                month DATE NOT NULL,
                reading REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (room_id) REFERENCES rooms(id)
            )
        ''')
        
        # Bảng Laundry (Giặt)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS laundry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                month DATE NOT NULL,
                num_people INTEGER NOT NULL,
                amount REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (room_id) REFERENCES rooms(id)
            )
        ''')
        
        # Bảng Expenses (Chi phí)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                description TEXT,
                amount REAL NOT NULL,
                room_id INTEGER,
                date DATE NOT NULL,
                paid_by_resident BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (room_id) REFERENCES rooms(id)
            )
        ''')
        
        # Bảng MonthlyBills (Hóa đơn hàng tháng)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monthly_bills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                resident_id INTEGER NOT NULL,
                month DATE NOT NULL,
                room_fee REAL,
                electricity_fee REAL,
                water_fee REAL,
                laundry_fee REAL,
                other_fees REAL,
                total_amount REAL,
                paid BOOLEAN DEFAULT 0,
                payment_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (room_id) REFERENCES rooms(id),
                FOREIGN KEY (resident_id) REFERENCES residents(id)
            )
        ''')
        
        # Bảng Settings (Cài đặt giá)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()

        # Migration: thêm cột mới cho monthly_bills nếu chưa có
        for col_name, col_type in [
            ('internet_trash_fee', 'REAL DEFAULT 0'),
            ('internet_trash_notes', 'TEXT'),
            ('elec_old_reading', 'REAL'),
            ('elec_new_reading', 'REAL'),
            ('num_residents', 'INTEGER DEFAULT 0'),
        ]:
            try:
                cursor.execute(
                    f'ALTER TABLE monthly_bills ADD COLUMN {col_name} {col_type}'
                )
            except sqlite3.OperationalError:
                pass  # Cột đã tồn tại
        self.conn.commit()

        self.init_default_settings()
    
    def init_default_settings(self):
        """Khởi tạo các cài đặt mặc định"""
        cursor = self.conn.cursor()
        
        settings = {
            'electricity_price': 3500,      # 3,500đ/1 số điện
            'water_price': 50000,           # 50,000đ/1 người/tháng
            'laundry_1person': 30000,       # 30,000đ
            'laundry_2person': 40000,       # 40,000đ
            'laundry_3person': 50000,       # 50,000đ
            'laundry_4plus': 60000,         # 60,000đ
            'trash_fee': 0,                 # Tiền rác
            'internet_fee': 0,              # Tiền internet
        }
        
        for key, value in settings.items():
            try:
                cursor.execute('INSERT INTO settings (key, value) VALUES (?, ?)', (key, value))
            except sqlite3.IntegrityError:
                pass  # Đã tồn tại
        
        self.conn.commit()
    
    # ===== PHÒNG (ROOMS) =====
    def add_room(self, name, price):
        """Thêm phòng mới"""
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO rooms (name, price, status) VALUES (?, ?, ?)',
                      (name, price, 'empty'))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_all_rooms(self):
        """Lấy tất cả phòng"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM rooms ORDER BY name')
        return cursor.fetchall()
    
    def get_empty_rooms(self):
        """Lấy các phòng trống"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, name FROM rooms WHERE status = "empty" ORDER BY name')
        return cursor.fetchall()
    
    def update_room_status(self, room_id, status):
        """Cập nhật trạng thái phòng"""
        cursor = self.conn.cursor()
        cursor.execute('UPDATE rooms SET status = ? WHERE id = ?', (status, room_id))
        self.conn.commit()

    def delete_room(self, room_id):
        """Xóa phòng và tất cả cư dân trong phòng"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM residents WHERE room_id = ?', (room_id,))
        cursor.execute('DELETE FROM electricity_meter WHERE room_id = ?', (room_id,))
        cursor.execute('DELETE FROM laundry WHERE room_id = ?', (room_id,))
        cursor.execute('DELETE FROM monthly_bills WHERE room_id = ?', (room_id,))
        cursor.execute('DELETE FROM rooms WHERE id = ?', (room_id,))
        self.conn.commit()
    
    # ===== CƯ DÂN (RESIDENTS) =====
    def add_resident(self, name, age, cccd, phone, room_id, check_in_date):
        """Thêm cư dân mới"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO residents (name, age, cccd, phone, room_id, check_in_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, age, cccd, phone, room_id, check_in_date))
        
        # Cập nhật trạng thái phòng
        self.update_room_status(room_id, 'occupied')
        self.conn.commit()
        return cursor.lastrowid
    
    def get_all_residents(self):
        """Lấy tất cả cư dân"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT residents.*, rooms.name as room_name 
            FROM residents 
            LEFT JOIN rooms ON residents.room_id = rooms.id
            ORDER BY residents.name
        ''')
        return cursor.fetchall()
    
    def get_resident_by_id(self, resident_id):
        """Lấy thông tin cư dân theo ID"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM residents WHERE id = ?', (resident_id,))
        return cursor.fetchone()
    
    def update_resident(self, resident_id, name, age, phone, notes):
        """Cập nhật thông tin cư dân"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE residents 
            SET name = ?, age = ?, phone = ?, notes = ?
            WHERE id = ?
        ''', (name, age, phone, notes, resident_id))
        self.conn.commit()
    
    def delete_resident(self, resident_id):
        """Xóa cư dân"""
        cursor = self.conn.cursor()
        resident = self.get_resident_by_id(resident_id)
        if resident:
            room_id = resident['room_id']
            cursor.execute('DELETE FROM residents WHERE id = ?', (resident_id,))
            # Mark room empty only when no residents remain after deletion
            cursor.execute(
                'SELECT COUNT(*) FROM residents WHERE room_id = ?', (room_id,)
            )
            remaining = cursor.fetchone()[0]
            if remaining == 0:
                self.update_room_status(room_id, 'empty')
        self.conn.commit()

    def get_residents_by_room(self, room_id):
        """Lấy danh sách cư dân theo phòng"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM residents WHERE room_id = ?', (room_id,))
        return cursor.fetchall()

    def get_residents_count_by_room(self, room_id):
        """Đếm số cư dân trong phòng"""
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT COUNT(*) FROM residents WHERE room_id = ?', (room_id,)
        )
        result = cursor.fetchone()
        return result[0] if result else 0
    
    # ===== ĐIỆN (ELECTRICITY) =====
    def add_electricity_reading(self, room_id, month, reading):
        """Ghi mốc điện"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO electricity_meter (room_id, month, reading)
            VALUES (?, ?, ?)
        ''', (room_id, month, reading))
        self.conn.commit()
    
    def get_electricity_readings(self, room_id):
        """Lấy mốc điện của phòng"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM electricity_meter 
            WHERE room_id = ? 
            ORDER BY month DESC
        ''', (room_id,))
        return cursor.fetchall()
    
    def calculate_electricity_fee(self, room_id, month):
        """Tính tiền điện"""
        cursor = self.conn.cursor()
        
        # Lấy mốc tháng hiện tại và tháng trước
        current_month = f"{month.year}-{month.month:02d}"
        prev_month_date = month - timedelta(days=30)
        prev_month = f"{prev_month_date.year}-{prev_month_date.month:02d}"
        
        cursor.execute('''
            SELECT reading FROM electricity_meter 
            WHERE room_id = ? AND month LIKE ?
            ORDER BY month DESC LIMIT 1
        ''', (room_id, f"{current_month}%"))
        current = cursor.fetchone()
        
        cursor.execute('''
            SELECT reading FROM electricity_meter 
            WHERE room_id = ? AND month LIKE ?
            ORDER BY month DESC LIMIT 1
        ''', (room_id, f"{prev_month}%"))
        previous = cursor.fetchone()
        
        if current and previous:
            usage = current[0] - previous[0]
            electricity_price = self.get_setting('electricity_price')
            return usage * electricity_price
        return 0
    
    # ===== NƯỚC (WATER) =====
    def calculate_water_fee(self, room_id, month):
        """Tính tiền nước dựa vào số người"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as num_people FROM residents 
            WHERE room_id = ?
        ''', (room_id,))
        result = cursor.fetchone()
        num_people = result[0] if result else 0
        
        water_price = self.get_setting('water_price')
        return num_people * water_price
    
    # ===== GIẶT (LAUNDRY) =====
    def add_laundry_record(self, room_id, month, num_people):
        """Ghi chép giặt"""
        laundry_fee = self.calculate_laundry_fee(num_people)
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO laundry (room_id, month, num_people, amount)
            VALUES (?, ?, ?, ?)
        ''', (room_id, month, num_people, laundry_fee))
        self.conn.commit()
    
    def calculate_laundry_fee(self, num_people):
        """Tính tiền giặt theo số người (20.000đ/người/tháng)"""
        return num_people * 20000
    
    # ===== CHI PHÍ (EXPENSES) =====
    def add_expense(self, exp_type, description, amount, room_id=None, paid_by_resident=False):
        """Thêm chi phí"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO expenses (type, description, amount, room_id, date, paid_by_resident)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (exp_type, description, amount, room_id, datetime.now().date(), paid_by_resident))
        self.conn.commit()
    
    def get_all_expenses(self):
        """Lấy tất cả chi phí"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM expenses ORDER BY date DESC')
        return cursor.fetchall()
    
    # ===== HÓA ĐƠN (BILLS) =====
    def create_monthly_bill(self, room_id, resident_id, month):
        """Tạo hóa đơn tháng"""
        from datetime import date
        
        # Tính các khoản phí
        room_fee = self.get_room_price(room_id)
        electricity_fee = self.calculate_electricity_fee(room_id, month)
        water_fee = self.calculate_water_fee(room_id, month)
        
        # Lấy tiền giặt và các khoản khác từ database
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT SUM(amount) FROM laundry 
            WHERE room_id = ? AND month = ?
        ''', (room_id, month))
        laundry_result = cursor.fetchone()
        laundry_fee = laundry_result[0] if laundry_result[0] else 0
        
        # Tính tổng
        total = room_fee + electricity_fee + water_fee + laundry_fee
        
        cursor.execute('''
            INSERT INTO monthly_bills 
            (room_id, resident_id, month, room_fee, electricity_fee, water_fee, laundry_fee, total_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (room_id, resident_id, month, room_fee, electricity_fee, water_fee, laundry_fee, total))
        self.conn.commit()
    
    def get_bills_by_month(self, month):
        """Lấy hóa đơn theo tháng"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM monthly_bills 
            WHERE month = ?
            ORDER BY room_id
        ''', (month,))
        return cursor.fetchall()
    
    def mark_bill_as_paid(self, bill_id):
        """Đánh dấu hóa đơn đã thanh toán"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE monthly_bills 
            SET paid = 1, payment_date = ?
            WHERE id = ?
        ''', (datetime.now().date(), bill_id))
        self.conn.commit()
    
    # ===== CÀI ĐẶT (SETTINGS) =====
    def get_setting(self, key):
        """Lấy giá trị cài đặt"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def update_setting(self, key, value):
        """Cập nhật cài đặt"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE settings SET value = ?, updated_at = CURRENT_TIMESTAMP
            WHERE key = ?
        ''', (value, key))
        self.conn.commit()
    
    # ===== THỐNG KÊ (STATISTICS) =====
    def get_statistics(self):
        """Lấy thống kê"""
        cursor = self.conn.cursor()
        
        # Tổng phòng
        cursor.execute('SELECT COUNT(*) FROM rooms')
        total_rooms = cursor.fetchone()[0]
        
        # Phòng trống
        cursor.execute('SELECT COUNT(*) FROM rooms WHERE status = "empty"')
        empty_rooms = cursor.fetchone()[0]
        
        # Tổng cư dân
        cursor.execute('SELECT COUNT(*) FROM residents')
        total_residents = cursor.fetchone()[0]
        
        return {
            'total_rooms': total_rooms,
            'empty_rooms': empty_rooms,
            'total_residents': total_residents,
            'occupied_rooms': total_rooms - empty_rooms
        }
    
    def get_profit_report(self, month):
        """Lấy báo cáo lợi nhuận"""
        cursor = self.conn.cursor()
        
        # Tổng doanh thu
        cursor.execute('''
            SELECT SUM(total_amount) FROM monthly_bills 
            WHERE month = ?
        ''', (month,))
        revenue = cursor.fetchone()[0] or 0
        
        # Tổng chi phí
        cursor.execute('''
            SELECT SUM(amount) FROM expenses 
            WHERE date LIKE ?
        ''', (f"{month}%",))
        expenses = cursor.fetchone()[0] or 0
        
        profit = revenue - expenses
        profit_percent = (profit / revenue * 100) if revenue > 0 else 0
        
        return {
            'revenue': revenue,
            'expenses': expenses,
            'profit': profit,
            'profit_percent': profit_percent
        }
    
    def get_room_price(self, room_id):
        """Lấy giá phòng"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT price FROM rooms WHERE id = ?', (room_id,))
        result = cursor.fetchone()
        return result[0] if result else 0

    def save_monthly_bill(self, room_id, month, room_fee, electricity_fee,
                          water_fee, laundry_fee, internet_trash_fee,
                          internet_trash_notes, elec_old_reading,
                          elec_new_reading, num_residents):
        """Lưu hóa đơn tháng (tạo mới hoặc cập nhật)"""
        total = room_fee + electricity_fee + water_fee + laundry_fee + internet_trash_fee
        cursor = self.conn.cursor()

        cursor.execute(
            'SELECT id FROM monthly_bills WHERE room_id = ? AND month = ?',
            (room_id, month)
        )
        existing = cursor.fetchone()

        if existing:
            cursor.execute('''
                UPDATE monthly_bills
                SET room_fee=?, electricity_fee=?, water_fee=?, laundry_fee=?,
                    internet_trash_fee=?, internet_trash_notes=?,
                    elec_old_reading=?, elec_new_reading=?, num_residents=?,
                    total_amount=?, paid=1, payment_date=?
                WHERE room_id=? AND month=?
            ''', (room_fee, electricity_fee, water_fee, laundry_fee,
                  internet_trash_fee, internet_trash_notes,
                  elec_old_reading, elec_new_reading, num_residents,
                  total, datetime.now().date(), room_id, month))
        else:
            cursor.execute('''
                INSERT INTO monthly_bills
                (room_id, resident_id, month, room_fee, electricity_fee, water_fee,
                 laundry_fee, internet_trash_fee, internet_trash_notes,
                 elec_old_reading, elec_new_reading, num_residents,
                 total_amount, paid, payment_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            ''', (room_id,
                  # resident_id is 0 because this bill is room-level, not per-resident
                  0,
                  month, room_fee, electricity_fee, water_fee, laundry_fee,
                  internet_trash_fee, internet_trash_notes,
                  elec_old_reading, elec_new_reading, num_residents,
                  total, datetime.now().date()))
        self.conn.commit()

    def get_bill_by_room_month(self, room_id, month):
        """Lấy hóa đơn theo phòng và tháng"""
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT * FROM monthly_bills WHERE room_id = ? AND month = ?',
            (room_id, month)
        )
        return cursor.fetchone()

    def close(self):
        """Đóng kết nối"""
        if self.conn:
            self.conn.close()
