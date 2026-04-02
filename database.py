import sqlite3
from datetime import datetime
import os


class Database:
    def __init__(self, db_name="phong_tro.db"):
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
                start_date TEXT,
                deposit REAL DEFAULT 0,
                billing_day INTEGER DEFAULT 1,
                status TEXT DEFAULT 'empty',
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Bảng Khách Trọ (Tenants)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tenants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                cccd TEXT,
                dob TEXT,
                hometown TEXT,
                phone TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
            )
        ''')

        # Bảng Số Điện (Electricity readings)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS electricity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                month TEXT NOT NULL,
                old_reading REAL DEFAULT 0,
                new_reading REAL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
                UNIQUE(room_id, month)
            )
        ''')

        # Bảng Số Nước (Water readings)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS water (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                month TEXT NOT NULL,
                old_reading REAL DEFAULT 0,
                new_reading REAL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
                UNIQUE(room_id, month)
            )
        ''')

        # Bảng Giặt (Laundry)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS laundry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                month TEXT NOT NULL,
                times INTEGER DEFAULT 0,
                amount REAL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
                UNIQUE(room_id, month)
            )
        ''')

        # Bảng Chi Phí Khác (Other expenses)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS other_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                month TEXT NOT NULL,
                amount REAL DEFAULT 0,
                note TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
                UNIQUE(room_id, month)
            )
        ''')

        # Bảng Cài Đặt (Settings)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')

        self.conn.commit()
        self._init_default_settings()

    def _init_default_settings(self):
        """Khởi tạo cài đặt mặc định"""
        defaults = {
            'electricity_price': '3500',
            'water_price': '15000',
            'laundry_price': '20000',
        }
        cursor = self.conn.cursor()
        for key, value in defaults.items():
            cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', (key, value))
        self.conn.commit()

    # ===== PHÒNG (ROOMS) =====
    def add_room(self, name, price, start_date, deposit, billing_day, notes=''):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO rooms (name, price, start_date, deposit, billing_day, status, notes)
            VALUES (?, ?, ?, ?, ?, 'empty', ?)
        ''', (name, price, start_date, deposit, billing_day, notes))
        self.conn.commit()
        return cursor.lastrowid

    def update_room(self, room_id, name, price, start_date, deposit, billing_day, notes=''):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE rooms SET name=?, price=?, start_date=?, deposit=?, billing_day=?, notes=?
            WHERE id=?
        ''', (name, price, start_date, deposit, billing_day, notes, room_id))
        self.conn.commit()

    def delete_room(self, room_id):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM rooms WHERE id=?', (room_id,))
        self.conn.commit()

    def get_all_rooms(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM rooms ORDER BY name')
        return cursor.fetchall()

    def get_room(self, room_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM rooms WHERE id=?', (room_id,))
        return cursor.fetchone()

    def update_room_status(self, room_id):
        """Cập nhật trạng thái phòng dựa vào số khách trọ"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM tenants WHERE room_id=?', (room_id,))
        count = cursor.fetchone()[0]
        status = 'occupied' if count > 0 else 'empty'
        cursor.execute('UPDATE rooms SET status=? WHERE id=?', (status, room_id))
        self.conn.commit()

    # ===== KHÁCH TRỌ (TENANTS) =====
    def add_tenant(self, room_id, name, cccd='', dob='', hometown='', phone=''):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO tenants (room_id, name, cccd, dob, hometown, phone)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (room_id, name, cccd or None, dob or None, hometown or None, phone or None))
        self.conn.commit()
        self.update_room_status(room_id)
        return cursor.lastrowid

    def update_tenant(self, tenant_id, name, cccd='', dob='', hometown='', phone=''):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE tenants SET name=?, cccd=?, dob=?, hometown=?, phone=?
            WHERE id=?
        ''', (name, cccd or None, dob or None, hometown or None, phone or None, tenant_id))
        self.conn.commit()

    def delete_tenant(self, tenant_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT room_id FROM tenants WHERE id=?', (tenant_id,))
        row = cursor.fetchone()
        cursor.execute('DELETE FROM tenants WHERE id=?', (tenant_id,))
        self.conn.commit()
        if row:
            self.update_room_status(row['room_id'])

    def get_tenants_by_room(self, room_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM tenants WHERE room_id=? ORDER BY name', (room_id,))
        return cursor.fetchall()

    def get_tenant(self, tenant_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM tenants WHERE id=?', (tenant_id,))
        return cursor.fetchone()

    def get_all_active_tenants(self):
        """Lấy tất cả khách trọ đang ở (kèm tên phòng)"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT t.*, r.name as room_name
            FROM tenants t
            JOIN rooms r ON t.room_id = r.id
            WHERE r.status = 'occupied'
            ORDER BY r.name, t.name
        ''')
        return cursor.fetchall()

    # ===== ĐIỆN (ELECTRICITY) =====
    def save_electricity(self, room_id, month, old_reading, new_reading):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO electricity (room_id, month, old_reading, new_reading)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(room_id, month) DO UPDATE SET
                old_reading=excluded.old_reading,
                new_reading=excluded.new_reading
        ''', (room_id, month, old_reading, new_reading))
        self.conn.commit()

    def get_electricity(self, room_id, month):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM electricity WHERE room_id=? AND month=?', (room_id, month))
        return cursor.fetchone()

    def get_electricity_history(self, room_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM electricity WHERE room_id=? ORDER BY month DESC', (room_id,))
        return cursor.fetchall()

    # ===== NƯỚC (WATER) =====
    def save_water(self, room_id, month, old_reading, new_reading):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO water (room_id, month, old_reading, new_reading)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(room_id, month) DO UPDATE SET
                old_reading=excluded.old_reading,
                new_reading=excluded.new_reading
        ''', (room_id, month, old_reading, new_reading))
        self.conn.commit()

    def get_water(self, room_id, month):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM water WHERE room_id=? AND month=?', (room_id, month))
        return cursor.fetchone()

    # ===== GIẶT (LAUNDRY) =====
    def save_laundry(self, room_id, month, times, amount):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO laundry (room_id, month, times, amount)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(room_id, month) DO UPDATE SET
                times=excluded.times,
                amount=excluded.amount
        ''', (room_id, month, times, amount))
        self.conn.commit()

    def get_laundry(self, room_id, month):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM laundry WHERE room_id=? AND month=?', (room_id, month))
        return cursor.fetchone()

    # ===== CHI PHÍ KHÁC (OTHER EXPENSES) =====
    def save_other_expense(self, room_id, month, amount, note=''):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO other_expenses (room_id, month, amount, note)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(room_id, month) DO UPDATE SET
                amount=excluded.amount,
                note=excluded.note
        ''', (room_id, month, amount, note))
        self.conn.commit()

    def get_other_expense(self, room_id, month):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM other_expenses WHERE room_id=? AND month=?', (room_id, month))
        return cursor.fetchone()

    # ===== CÀI ĐẶT (SETTINGS) =====
    def get_setting(self, key, default=None):
        cursor = self.conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key=?', (key,))
        row = cursor.fetchone()
        return row['value'] if row else default

    def set_setting(self, key, value):
        cursor = self.conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, str(value)))
        self.conn.commit()

    # ===== THỐNG KÊ (STATISTICS) =====
    def get_statistics(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM rooms')
        total_rooms = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM rooms WHERE status="empty"')
        empty_rooms = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM tenants')
        total_tenants = cursor.fetchone()[0]
        return {
            'total_rooms': total_rooms,
            'empty_rooms': empty_rooms,
            'total_tenants': total_tenants,
        }

    # ===== TÍNH HÓA ĐƠN (BILLING) =====
    def get_bill_data(self, room_id, month):
        """Lấy tất cả dữ liệu để tính hóa đơn"""
        room = self.get_room(room_id)
        if not room:
            return None

        elec = self.get_electricity(room_id, month)
        water = self.get_water(room_id, month)
        laundry = self.get_laundry(room_id, month)
        other = self.get_other_expense(room_id, month)

        elec_price = float(self.get_setting('electricity_price', 3500))
        water_price = float(self.get_setting('water_price', 15000))

        elec_usage = 0
        elec_fee = 0
        if elec:
            elec_usage = max(0, elec['new_reading'] - elec['old_reading'])
            elec_fee = elec_usage * elec_price

        water_usage = 0
        water_fee = 0
        if water:
            water_usage = max(0, water['new_reading'] - water['old_reading'])
            water_fee = water_usage * water_price

        laundry_fee = laundry['amount'] if laundry else 0
        other_fee = other['amount'] if other else 0
        other_note = other['note'] if other else ''

        total = room['price'] + elec_fee + water_fee + laundry_fee + other_fee

        return {
            'room_id': room_id,
            'room_name': room['name'],
            'room_fee': room['price'],
            'elec_old': elec['old_reading'] if elec else 0,
            'elec_new': elec['new_reading'] if elec else 0,
            'elec_usage': elec_usage,
            'elec_price': elec_price,
            'elec_fee': elec_fee,
            'water_old': water['old_reading'] if water else 0,
            'water_new': water['new_reading'] if water else 0,
            'water_usage': water_usage,
            'water_price': water_price,
            'water_fee': water_fee,
            'laundry_fee': laundry_fee,
            'other_fee': other_fee,
            'other_note': other_note,
            'total': total,
            'month': month,
        }

    # ===== THÔNG BÁO HẠN TIỀN (BILLING NOTIFICATIONS) =====
    def get_rooms_due_today(self):
        """Lấy các phòng tới hạn đóng tiền hôm nay"""
        today_day = datetime.now().day
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM rooms
            WHERE billing_day = ? AND status = 'occupied'
            ORDER BY name
        ''', (today_day,))
        return cursor.fetchall()

    def close(self):
        """Đóng kết nối database"""
        if self.conn:
            self.conn.close()
