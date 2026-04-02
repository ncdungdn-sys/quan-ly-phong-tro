import sqlite3
from datetime import datetime
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
        self.conn.execute("PRAGMA foreign_keys = ON")
        cursor = self.conn.cursor()

        # Bảng Phòng (Rooms)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                price REAL NOT NULL DEFAULT 0,
                start_date DATE,
                deposit REAL DEFAULT 0,
                billing_day INTEGER DEFAULT 1,
                notes TEXT,
                status TEXT DEFAULT 'empty'
            )
        ''')

        # Bảng Khách Trọ (Residents) — CCCD is optional and intentionally not unique-constrained,
        # so multiple residents without a CCCD can coexist in the same room.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS residents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                cccd TEXT,
                date_of_birth DATE,
                hometown TEXT,
                phone TEXT,
                FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
            )
        ''')

        # Bảng Số Điện (Electricity Readings) — old + new per room per month
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS electricity_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                month TEXT NOT NULL,
                old_reading REAL DEFAULT 0,
                new_reading REAL DEFAULT 0,
                UNIQUE(room_id, month),
                FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
            )
        ''')

        # Bảng Số Nước (Water Readings) — old + new per room per month
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS water_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                month TEXT NOT NULL,
                old_reading REAL DEFAULT 0,
                new_reading REAL DEFAULT 0,
                UNIQUE(room_id, month),
                FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
            )
        ''')

        # Bảng Giặt (Laundry) — per room per month
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS laundry_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                month TEXT NOT NULL,
                times INTEGER DEFAULT 0,
                amount REAL DEFAULT 0,
                UNIQUE(room_id, month),
                FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
            )
        ''')

        # Bảng Chi Phí Khác (Other Monthly Expenses) — per room per month
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monthly_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                month TEXT NOT NULL,
                amount REAL DEFAULT 0,
                notes TEXT,
                UNIQUE(room_id, month),
                FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
            )
        ''')

        # Bảng Cài Đặt (Settings)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value REAL NOT NULL
            )
        ''')

        self.conn.commit()
        self._init_default_settings()

    def _init_default_settings(self):
        """Khởi tạo giá trị mặc định"""
        cursor = self.conn.cursor()
        defaults = [
            ('electricity_price', 3500),   # đ/kWh
            ('water_price', 15000),        # đ/khối
            ('laundry_price', 30000),      # đ/lần
        ]
        for key, value in defaults:
            cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', (key, value))
        self.conn.commit()

    # ===== PHÒNG (ROOMS) =====

    def add_room(self, name, price, start_date=None, deposit=0, billing_day=1, notes=''):
        """Thêm phòng mới"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO rooms (name, price, start_date, deposit, billing_day, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, 'empty')
        ''', (name, price, start_date, deposit, billing_day, notes or None))
        self.conn.commit()
        return cursor.lastrowid

    def update_room(self, room_id, name, price, start_date, deposit, billing_day, notes):
        """Cập nhật thông tin phòng"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE rooms SET name=?, price=?, start_date=?, deposit=?, billing_day=?, notes=?
            WHERE id=?
        ''', (name, price, start_date, deposit, billing_day, notes or None, room_id))
        self.conn.commit()

    def delete_room(self, room_id):
        """Xóa phòng (và tất cả dữ liệu liên quan qua CASCADE)"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM rooms WHERE id=?', (room_id,))
        self.conn.commit()

    def get_all_rooms(self):
        """Lấy tất cả phòng kèm số lượng khách trọ"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT r.*, COUNT(res.id) AS resident_count
            FROM rooms r
            LEFT JOIN residents res ON r.id = res.room_id
            GROUP BY r.id
            ORDER BY r.name
        ''')
        return cursor.fetchall()

    def get_room_by_id(self, room_id):
        """Lấy thông tin một phòng"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM rooms WHERE id=?', (room_id,))
        return cursor.fetchone()

    def _refresh_room_status(self, room_id):
        """Cập nhật trạng thái phòng dựa trên số khách"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM residents WHERE room_id=?', (room_id,))
        count = cursor.fetchone()[0]
        status = 'occupied' if count > 0 else 'empty'
        cursor.execute('UPDATE rooms SET status=? WHERE id=?', (status, room_id))
        self.conn.commit()

    # ===== KHÁCH TRỌ (RESIDENTS) =====

    def add_resident(self, room_id, name, cccd=None, date_of_birth=None, hometown=None, phone=None):
        """Thêm khách trọ"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO residents (room_id, name, cccd, date_of_birth, hometown, phone)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (room_id, name, cccd or None, date_of_birth or None, hometown or None, phone or None))
        self.conn.commit()
        self._refresh_room_status(room_id)
        return cursor.lastrowid

    def update_resident(self, resident_id, name, cccd=None, date_of_birth=None, hometown=None, phone=None):
        """Cập nhật thông tin khách trọ"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE residents SET name=?, cccd=?, date_of_birth=?, hometown=?, phone=?
            WHERE id=?
        ''', (name, cccd or None, date_of_birth or None, hometown or None, phone or None, resident_id))
        self.conn.commit()

    def delete_resident(self, resident_id):
        """Xóa khách trọ"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT room_id FROM residents WHERE id=?', (resident_id,))
        row = cursor.fetchone()
        cursor.execute('DELETE FROM residents WHERE id=?', (resident_id,))
        self.conn.commit()
        if row:
            self._refresh_room_status(row['room_id'])

    def get_resident_by_id(self, resident_id):
        """Lấy thông tin một khách trọ"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM residents WHERE id=?', (resident_id,))
        return cursor.fetchone()

    def get_residents_by_room(self, room_id):
        """Lấy danh sách khách trọ của một phòng"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM residents WHERE room_id=? ORDER BY name', (room_id,))
        return cursor.fetchall()

    def get_all_residents(self):
        """Lấy tất cả khách trọ kèm tên phòng"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT res.*, r.name AS room_name
            FROM residents res
            JOIN rooms r ON res.room_id = r.id
            ORDER BY r.name, res.name
        ''')
        return cursor.fetchall()

    # ===== SỐ ĐIỆN (ELECTRICITY) =====

    def save_electricity_reading(self, room_id, month, old_reading, new_reading):
        """Lưu số điện tháng"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO electricity_readings (room_id, month, old_reading, new_reading)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(room_id, month) DO UPDATE SET
                old_reading=excluded.old_reading,
                new_reading=excluded.new_reading
        ''', (room_id, month, old_reading, new_reading))
        self.conn.commit()

    def get_electricity_reading(self, room_id, month):
        """Lấy số điện theo tháng"""
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT * FROM electricity_readings WHERE room_id=? AND month=?',
            (room_id, month)
        )
        return cursor.fetchone()

    def get_electricity_readings_by_room(self, room_id):
        """Lấy tất cả số điện của phòng"""
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT * FROM electricity_readings WHERE room_id=? ORDER BY month DESC',
            (room_id,)
        )
        return cursor.fetchall()

    # ===== SỐ NƯỚC (WATER) =====

    def save_water_reading(self, room_id, month, old_reading, new_reading):
        """Lưu số nước tháng"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO water_readings (room_id, month, old_reading, new_reading)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(room_id, month) DO UPDATE SET
                old_reading=excluded.old_reading,
                new_reading=excluded.new_reading
        ''', (room_id, month, old_reading, new_reading))
        self.conn.commit()

    def get_water_reading(self, room_id, month):
        """Lấy số nước theo tháng"""
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT * FROM water_readings WHERE room_id=? AND month=?',
            (room_id, month)
        )
        return cursor.fetchone()

    # ===== GIẶT (LAUNDRY) =====

    def save_laundry_record(self, room_id, month, times, amount):
        """Lưu thông tin giặt tháng"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO laundry_records (room_id, month, times, amount)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(room_id, month) DO UPDATE SET
                times=excluded.times,
                amount=excluded.amount
        ''', (room_id, month, times, amount))
        self.conn.commit()

    def get_laundry_record(self, room_id, month):
        """Lấy thông tin giặt theo tháng"""
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT * FROM laundry_records WHERE room_id=? AND month=?',
            (room_id, month)
        )
        return cursor.fetchone()

    # ===== CHI PHÍ KHÁC (OTHER EXPENSES) =====

    def save_monthly_expense(self, room_id, month, amount, notes):
        """Lưu chi phí khác tháng"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO monthly_expenses (room_id, month, amount, notes)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(room_id, month) DO UPDATE SET
                amount=excluded.amount,
                notes=excluded.notes
        ''', (room_id, month, amount, notes or None))
        self.conn.commit()

    def get_monthly_expense(self, room_id, month):
        """Lấy chi phí khác theo tháng"""
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT * FROM monthly_expenses WHERE room_id=? AND month=?',
            (room_id, month)
        )
        return cursor.fetchone()

    # ===== CÀI ĐẶT (SETTINGS) =====

    def get_setting(self, key):
        """Lấy giá trị cài đặt"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key=?', (key,))
        row = cursor.fetchone()
        return row['value'] if row else None

    def update_setting(self, key, value):
        """Cập nhật cài đặt"""
        cursor = self.conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
        self.conn.commit()

    def get_all_settings(self):
        """Lấy tất cả cài đặt"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM settings')
        return {row['key']: row['value'] for row in cursor.fetchall()}

    # ===== THỐNG KÊ (STATISTICS) =====

    def get_statistics(self):
        """Lấy thống kê tổng quan"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM rooms')
        total_rooms = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM rooms WHERE status="empty"')
        empty_rooms = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM residents')
        total_residents = cursor.fetchone()[0]
        return {
            'total_rooms': total_rooms,
            'empty_rooms': empty_rooms,
            'total_residents': total_residents,
            'occupied_rooms': total_rooms - empty_rooms,
        }

    def close(self):
        """Đóng kết nối"""
        if self.conn:
            self.conn.close()
