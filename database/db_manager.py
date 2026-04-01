"""
Quản lý cơ sở dữ liệu SQLite cho ứng dụng Quản Lý Phòng Trọ.
Tạo tất cả bảng và cung cấp các hàm CRUD cơ bản.
"""
import sqlite3
import os
from datetime import datetime

# Đường dẫn file database
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "phong_tro.db")


def get_connection():
    """Tạo và trả về kết nối database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Trả về dict-like rows
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database():
    """Khởi tạo database - tạo tất cả bảng nếu chưa tồn tại."""
    conn = get_connection()
    cursor = conn.cursor()

    # Bảng Rooms - Thông tin các phòng
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT NOT NULL UNIQUE,
            price REAL NOT NULL DEFAULT 0,
            description TEXT,
            status TEXT NOT NULL DEFAULT 'empty',
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # Bảng Residents - Thông tin cư dân
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Residents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            full_name TEXT NOT NULL,
            age INTEGER,
            id_card TEXT,
            phone TEXT,
            notes TEXT,
            check_in_date TEXT NOT NULL,
            check_out_date TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (room_id) REFERENCES Rooms(id)
        )
    """)

    # Bảng Settings - Cài đặt giá cả dịch vụ
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL UNIQUE,
            value TEXT NOT NULL,
            description TEXT,
            updated_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # Bảng ElectricityMeter - Ghi số điện
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ElectricityMeter (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            month INTEGER NOT NULL,
            year INTEGER NOT NULL,
            old_reading REAL NOT NULL DEFAULT 0,
            new_reading REAL NOT NULL DEFAULT 0,
            units_used REAL GENERATED ALWAYS AS (new_reading - old_reading) STORED,
            recorded_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (room_id) REFERENCES Rooms(id),
            UNIQUE(room_id, month, year)
        )
    """)

    # Bảng RoomExpenses - Chi phí phát sinh theo phòng
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS RoomExpenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            month INTEGER NOT NULL,
            year INTEGER NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL DEFAULT 0,
            paid_by TEXT NOT NULL DEFAULT 'owner',
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (room_id) REFERENCES Rooms(id)
        )
    """)

    # Bảng Expenses - Chi phí chung
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month INTEGER NOT NULL,
            year INTEGER NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL DEFAULT 0,
            category TEXT DEFAULT 'general',
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # Bảng MonthlyBills - Hóa đơn hàng tháng
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS MonthlyBills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            resident_id INTEGER,
            month INTEGER NOT NULL,
            year INTEGER NOT NULL,
            rent_amount REAL DEFAULT 0,
            electricity_amount REAL DEFAULT 0,
            water_amount REAL DEFAULT 0,
            laundry_amount REAL DEFAULT 0,
            garbage_amount REAL DEFAULT 0,
            internet_amount REAL DEFAULT 0,
            room_expense_amount REAL DEFAULT 0,
            other_amount REAL DEFAULT 0,
            total_amount REAL DEFAULT 0,
            paid_amount REAL DEFAULT 0,
            status TEXT DEFAULT 'unpaid',
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            updated_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (room_id) REFERENCES Rooms(id),
            FOREIGN KEY (resident_id) REFERENCES Residents(id),
            UNIQUE(room_id, month, year)
        )
    """)

    # Bảng Transactions - Lịch sử giao dịch
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_id INTEGER,
            room_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            transaction_type TEXT NOT NULL,
            description TEXT,
            transaction_date TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (bill_id) REFERENCES MonthlyBills(id),
            FOREIGN KEY (room_id) REFERENCES Rooms(id)
        )
    """)

    # Bảng LaundryRecords - Ghi chép giặt
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS LaundryRecords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            month INTEGER NOT NULL,
            year INTEGER NOT NULL,
            num_people INTEGER NOT NULL DEFAULT 1,
            amount REAL NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (room_id) REFERENCES Rooms(id),
            UNIQUE(room_id, month, year)
        )
    """)

    conn.commit()

    # Khởi tạo dữ liệu mặc định
    _init_default_data(cursor, conn)

    conn.close()


def _init_default_data(cursor, conn):
    """Khởi tạo dữ liệu mặc định cho hệ thống."""
    # Tạo 7 phòng mặc định
    rooms = [
        ("P101", 1500000, "Phòng tầng 1"),
        ("P102", 1500000, "Phòng tầng 1"),
        ("P201", 1800000, "Phòng tầng 2"),
        ("P202", 1800000, "Phòng tầng 2"),
        ("P301", 2000000, "Phòng tầng 3"),
        ("P302", 2000000, "Phòng tầng 3"),
        ("P401", 2200000, "Phòng tầng 4 - View đẹp"),
    ]

    for room_num, price, desc in rooms:
        cursor.execute("""
            INSERT OR IGNORE INTO Rooms (room_number, price, description, status)
            VALUES (?, ?, ?, 'empty')
        """, (room_num, price, desc))

    # Cài đặt giá mặc định
    settings = [
        ("electricity_price", "3500", "Giá điện (đ/số)"),
        ("water_price_per_person", "50000", "Tiền nước mỗi người (đ/tháng)"),
        ("laundry_1_person", "30000", "Tiền giặt 1 người"),
        ("laundry_2_person", "40000", "Tiền giặt 2 người"),
        ("laundry_3_person", "50000", "Tiền giặt 3 người"),
        ("laundry_4plus_person", "60000", "Tiền giặt 4+ người"),
        ("garbage_fee", "0", "Tiền rác mặc định"),
        ("internet_fee", "0", "Tiền internet mặc định"),
        ("backup_enabled", "1", "Bật backup tự động"),
        ("backup_interval_days", "7", "Số ngày backup một lần"),
    ]

    for key, value, desc in settings:
        cursor.execute("""
            INSERT OR IGNORE INTO Settings (key, value, description)
            VALUES (?, ?, ?)
        """, (key, value, desc))

    conn.commit()


# ==================== ROOMS ====================

def get_all_rooms():
    """Lấy tất cả phòng."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Rooms ORDER BY room_number")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_room_by_id(room_id):
    """Lấy thông tin một phòng theo ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Rooms WHERE id = ?", (room_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_room_price(room_id, price):
    """Cập nhật giá phòng."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE Rooms SET price = ? WHERE id = ?", (price, room_id))
    conn.commit()
    conn.close()


def update_room_status(room_id, status):
    """Cập nhật trạng thái phòng (empty/occupied)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE Rooms SET status = ? WHERE id = ?", (status, room_id))
    conn.commit()
    conn.close()


# ==================== RESIDENTS ====================

def get_all_residents(active_only=True):
    """Lấy tất cả cư dân."""
    conn = get_connection()
    cursor = conn.cursor()
    if active_only:
        cursor.execute("""
            SELECT r.*, rm.room_number FROM Residents r
            JOIN Rooms rm ON r.room_id = rm.id
            WHERE r.is_active = 1
            ORDER BY rm.room_number
        """)
    else:
        cursor.execute("""
            SELECT r.*, rm.room_number FROM Residents r
            JOIN Rooms rm ON r.room_id = rm.id
            ORDER BY rm.room_number, r.is_active DESC
        """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_residents_by_room(room_id, active_only=True):
    """Lấy cư dân theo phòng."""
    conn = get_connection()
    cursor = conn.cursor()
    if active_only:
        cursor.execute(
            "SELECT * FROM Residents WHERE room_id = ? AND is_active = 1",
            (room_id,)
        )
    else:
        cursor.execute("SELECT * FROM Residents WHERE room_id = ?", (room_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_resident(room_id, full_name, age, id_card, phone, notes, check_in_date):
    """Thêm cư dân mới."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Residents (room_id, full_name, age, id_card, phone, notes, check_in_date, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
    """, (room_id, full_name, age, id_card, phone, notes, check_in_date))
    resident_id = cursor.lastrowid
    # Cập nhật trạng thái phòng
    cursor.execute("UPDATE Rooms SET status = 'occupied' WHERE id = ?", (room_id,))
    conn.commit()
    conn.close()
    return resident_id


def update_resident(resident_id, full_name, age, id_card, phone, notes, check_in_date):
    """Cập nhật thông tin cư dân."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Residents
        SET full_name = ?, age = ?, id_card = ?, phone = ?, notes = ?, check_in_date = ?
        WHERE id = ?
    """, (full_name, age, id_card, phone, notes, check_in_date, resident_id))
    conn.commit()
    conn.close()


def checkout_resident(resident_id, check_out_date=None):
    """Cư dân trả phòng."""
    if not check_out_date:
        check_out_date = datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Residents SET is_active = 0, check_out_date = ?
        WHERE id = ?
    """, (check_out_date, resident_id))
    # Lấy room_id để kiểm tra còn ai không
    cursor.execute("SELECT room_id FROM Residents WHERE id = ?", (resident_id,))
    row = cursor.fetchone()
    if row:
        room_id = row["room_id"]
        cursor.execute(
            "SELECT COUNT(*) as cnt FROM Residents WHERE room_id = ? AND is_active = 1",
            (room_id,)
        )
        count_row = cursor.fetchone()
        if count_row and count_row["cnt"] == 0:
            cursor.execute("UPDATE Rooms SET status = 'empty' WHERE id = ?", (room_id,))
    conn.commit()
    conn.close()


def delete_resident(resident_id):
    """Xóa cư dân (xóa hoàn toàn)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT room_id FROM Residents WHERE id = ?", (resident_id,))
    row = cursor.fetchone()
    cursor.execute("DELETE FROM Residents WHERE id = ?", (resident_id,))
    if row:
        room_id = row["room_id"]
        cursor.execute(
            "SELECT COUNT(*) as cnt FROM Residents WHERE room_id = ? AND is_active = 1",
            (room_id,)
        )
        count_row = cursor.fetchone()
        if count_row and count_row["cnt"] == 0:
            cursor.execute("UPDATE Rooms SET status = 'empty' WHERE id = ?", (room_id,))
    conn.commit()
    conn.close()


# ==================== SETTINGS ====================

def get_setting(key, default=None):
    """Lấy giá trị cài đặt theo key."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM Settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row["value"]
    return default


def get_all_settings():
    """Lấy tất cả cài đặt."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Settings ORDER BY key")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_setting(key, value):
    """Cập nhật cài đặt."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Settings (key, value, updated_at)
        VALUES (?, ?, datetime('now', 'localtime'))
        ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = datetime('now', 'localtime')
    """, (key, value, value))
    conn.commit()
    conn.close()


# ==================== ELECTRICITY ====================

def get_electricity_reading(room_id, month, year):
    """Lấy ghi số điện của phòng theo tháng."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM ElectricityMeter
        WHERE room_id = ? AND month = ? AND year = ?
    """, (room_id, month, year))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_electricity_readings_by_month(month, year):
    """Lấy tất cả ghi số điện theo tháng."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.*, r.room_number FROM ElectricityMeter e
        JOIN Rooms r ON e.room_id = r.id
        WHERE e.month = ? AND e.year = ?
        ORDER BY r.room_number
    """, (month, year))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def save_electricity_reading(room_id, month, year, old_reading, new_reading):
    """Lưu/cập nhật ghi số điện."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO ElectricityMeter (room_id, month, year, old_reading, new_reading)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(room_id, month, year) DO UPDATE
        SET old_reading = ?, new_reading = ?, recorded_at = datetime('now', 'localtime')
    """, (room_id, month, year, old_reading, new_reading, old_reading, new_reading))
    conn.commit()
    conn.close()


def get_last_electricity_reading(room_id, before_month, before_year):
    """Lấy ghi số điện mới nhất trước tháng chỉ định."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM ElectricityMeter
        WHERE room_id = ?
        AND (year < ? OR (year = ? AND month < ?))
        ORDER BY year DESC, month DESC
        LIMIT 1
    """, (room_id, before_year, before_year, before_month))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# ==================== LAUNDRY ====================

def get_laundry_record(room_id, month, year):
    """Lấy ghi chép giặt của phòng theo tháng."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM LaundryRecords
        WHERE room_id = ? AND month = ? AND year = ?
    """, (room_id, month, year))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_laundry_records_by_month(month, year):
    """Lấy tất cả ghi chép giặt theo tháng."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT l.*, r.room_number FROM LaundryRecords l
        JOIN Rooms r ON l.room_id = r.id
        WHERE l.month = ? AND l.year = ?
        ORDER BY r.room_number
    """, (month, year))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def save_laundry_record(room_id, month, year, num_people, amount):
    """Lưu/cập nhật ghi chép giặt."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO LaundryRecords (room_id, month, year, num_people, amount)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(room_id, month, year) DO UPDATE
        SET num_people = ?, amount = ?, created_at = datetime('now', 'localtime')
    """, (room_id, month, year, num_people, amount, num_people, amount))
    conn.commit()
    conn.close()


# ==================== EXPENSES ====================

def get_expenses_by_month(month, year):
    """Lấy chi phí chung theo tháng."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM Expenses
        WHERE month = ? AND year = ?
        ORDER BY created_at DESC
    """, (month, year))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_expense(month, year, description, amount, category="general"):
    """Thêm chi phí chung."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Expenses (month, year, description, amount, category)
        VALUES (?, ?, ?, ?, ?)
    """, (month, year, description, amount, category))
    expense_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return expense_id


def delete_expense(expense_id):
    """Xóa chi phí chung."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()


def get_room_expenses_by_month(month, year):
    """Lấy chi phí phòng theo tháng."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT re.*, r.room_number FROM RoomExpenses re
        JOIN Rooms r ON re.room_id = r.id
        WHERE re.month = ? AND re.year = ?
        ORDER BY r.room_number
    """, (month, year))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_room_expenses_by_room_month(room_id, month, year):
    """Lấy chi phí phòng theo phòng và tháng."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM RoomExpenses
        WHERE room_id = ? AND month = ? AND year = ?
    """, (room_id, month, year))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_room_expense(room_id, month, year, description, amount, paid_by="owner"):
    """Thêm chi phí phát sinh theo phòng."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO RoomExpenses (room_id, month, year, description, amount, paid_by)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (room_id, month, year, description, amount, paid_by))
    expense_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return expense_id


def delete_room_expense(expense_id):
    """Xóa chi phí phòng."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM RoomExpenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()


# ==================== MONTHLY BILLS ====================

def get_bill(room_id, month, year):
    """Lấy hóa đơn của phòng theo tháng."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.*, r.room_number FROM MonthlyBills b
        JOIN Rooms r ON b.room_id = r.id
        WHERE b.room_id = ? AND b.month = ? AND b.year = ?
    """, (room_id, month, year))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_bills_by_month(month, year):
    """Lấy tất cả hóa đơn theo tháng."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.*, r.room_number FROM MonthlyBills b
        JOIN Rooms r ON b.room_id = r.id
        WHERE b.month = ? AND b.year = ?
        ORDER BY r.room_number
    """, (month, year))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def save_bill(room_id, resident_id, month, year, rent_amount, electricity_amount,
              water_amount, laundry_amount, garbage_amount, internet_amount,
              room_expense_amount, other_amount, notes=""):
    """Lưu/cập nhật hóa đơn."""
    total = (rent_amount + electricity_amount + water_amount + laundry_amount +
             garbage_amount + internet_amount + room_expense_amount + other_amount)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO MonthlyBills
        (room_id, resident_id, month, year, rent_amount, electricity_amount,
         water_amount, laundry_amount, garbage_amount, internet_amount,
         room_expense_amount, other_amount, total_amount, notes, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
        ON CONFLICT(room_id, month, year) DO UPDATE SET
        resident_id = ?, rent_amount = ?, electricity_amount = ?,
        water_amount = ?, laundry_amount = ?, garbage_amount = ?,
        internet_amount = ?, room_expense_amount = ?, other_amount = ?,
        total_amount = ?, notes = ?, updated_at = datetime('now', 'localtime')
    """, (
        room_id, resident_id, month, year, rent_amount, electricity_amount,
        water_amount, laundry_amount, garbage_amount, internet_amount,
        room_expense_amount, other_amount, total, notes,
        resident_id, rent_amount, electricity_amount,
        water_amount, laundry_amount, garbage_amount,
        internet_amount, room_expense_amount, other_amount,
        total, notes
    ))
    bill_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return bill_id


def update_bill_payment(bill_id, paid_amount, status):
    """Cập nhật trạng thái thanh toán hóa đơn."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE MonthlyBills
        SET paid_amount = ?, status = ?, updated_at = datetime('now', 'localtime')
        WHERE id = ?
    """, (paid_amount, status, bill_id))
    conn.commit()
    conn.close()


def add_transaction(bill_id, room_id, amount, transaction_type, description=""):
    """Thêm giao dịch."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Transactions (bill_id, room_id, amount, transaction_type, description)
        VALUES (?, ?, ?, ?, ?)
    """, (bill_id, room_id, amount, transaction_type, description))
    conn.commit()
    conn.close()


def get_transactions(room_id=None, month=None, year=None):
    """Lấy lịch sử giao dịch."""
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT t.*, r.room_number FROM Transactions t
        JOIN Rooms r ON t.room_id = r.id
        WHERE 1=1
    """
    params = []
    if room_id:
        query += " AND t.room_id = ?"
        params.append(room_id)
    if month and year:
        # Use date range comparison for index-friendly filtering
        start_date = f"{year}-{month:02d}-01"
        # Compute next month start for upper bound
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1
        end_date = f"{next_year}-{next_month:02d}-01"
        query += " AND t.transaction_date >= ? AND t.transaction_date < ?"
        params.append(start_date)
        params.append(end_date)
    query += " ORDER BY t.transaction_date DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ==================== REPORTS ====================

def get_monthly_summary(month, year):
    """Lấy tổng kết tháng."""
    conn = get_connection()
    cursor = conn.cursor()

    # Tổng doanh thu từ hóa đơn (đã thanh toán)
    cursor.execute("""
        SELECT COALESCE(SUM(total_amount), 0) as total_revenue,
               COALESCE(SUM(paid_amount), 0) as paid_revenue,
               COUNT(*) as total_bills,
               SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) as paid_bills
        FROM MonthlyBills
        WHERE month = ? AND year = ?
    """, (month, year))
    revenue_row = cursor.fetchone()

    # Tổng chi phí chung
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) as total_expenses
        FROM Expenses
        WHERE month = ? AND year = ?
    """, (month, year))
    expense_row = cursor.fetchone()

    # Chi phí phòng do chủ chịu
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) as owner_expenses
        FROM RoomExpenses
        WHERE month = ? AND year = ? AND paid_by = 'owner'
    """, (month, year))
    room_expense_row = cursor.fetchone()

    conn.close()

    total_revenue = revenue_row["total_revenue"] if revenue_row else 0
    paid_revenue = revenue_row["paid_revenue"] if revenue_row else 0
    total_bills = revenue_row["total_bills"] if revenue_row else 0
    paid_bills = revenue_row["paid_bills"] if revenue_row else 0
    total_expenses = expense_row["total_expenses"] if expense_row else 0
    owner_expenses = room_expense_row["owner_expenses"] if room_expense_row else 0

    total_cost = total_expenses + owner_expenses
    profit = paid_revenue - total_cost

    return {
        "month": month,
        "year": year,
        "total_revenue": total_revenue,
        "paid_revenue": paid_revenue,
        "total_bills": total_bills,
        "paid_bills": paid_bills,
        "total_expenses": total_expenses,
        "owner_expenses": owner_expenses,
        "total_cost": total_cost,
        "profit": profit,
    }


def get_yearly_summary(year):
    """Lấy tổng kết theo năm."""
    monthly_summaries = []
    for month in range(1, 13):
        summary = get_monthly_summary(month, year)
        monthly_summaries.append(summary)
    return monthly_summaries


def get_dashboard_stats():
    """Lấy thống kê cho Dashboard."""
    conn = get_connection()
    cursor = conn.cursor()

    # Tổng số phòng
    cursor.execute("SELECT COUNT(*) as total FROM Rooms")
    total_rooms = cursor.fetchone()["total"]

    # Số phòng trống
    cursor.execute("SELECT COUNT(*) as empty FROM Rooms WHERE status = 'empty'")
    empty_rooms = cursor.fetchone()["empty"]

    # Tổng cư dân đang ở
    cursor.execute("SELECT COUNT(*) as total FROM Residents WHERE is_active = 1")
    total_residents = cursor.fetchone()["total"]

    # Tháng hiện tại
    now = datetime.now()
    month, year = now.month, now.year

    # Doanh thu tháng này
    cursor.execute("""
        SELECT COALESCE(SUM(total_amount), 0) as revenue,
               COALESCE(SUM(paid_amount), 0) as paid
        FROM MonthlyBills
        WHERE month = ? AND year = ?
    """, (month, year))
    revenue_row = cursor.fetchone()

    # Chi phí tháng này
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) as expenses
        FROM Expenses WHERE month = ? AND year = ?
    """, (month, year))
    expense_row = cursor.fetchone()

    conn.close()

    revenue = revenue_row["revenue"] if revenue_row else 0
    paid = revenue_row["paid"] if revenue_row else 0
    expenses = expense_row["expenses"] if expense_row else 0

    return {
        "total_rooms": total_rooms,
        "empty_rooms": empty_rooms,
        "occupied_rooms": total_rooms - empty_rooms,
        "total_residents": total_residents,
        "monthly_revenue": revenue,
        "monthly_paid": paid,
        "monthly_expenses": expenses,
        "monthly_profit": paid - expenses,
    }
