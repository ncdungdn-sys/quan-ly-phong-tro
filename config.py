# ===== CẤU HÌNH ỨNG DỤNG =====

# Thông tin ứng dụng
APP_NAME = "Quản Lý Phòng Trọ"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Room Management System"

# Cơ sở dữ liệu
DATABASE_NAME = "room_management.db"

# Cửa sổ ứng dụng
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 700
WINDOW_TITLE = "📁 Quản Lý Phòng Trọ v1.0"

# Giá cả mặc định (VND)
DEFAULT_PRICES = {
    'electricity_per_unit': 3500,      # 3,500đ/1 số điện
    'water_per_person': 50000,         # 50,000đ/1 người/tháng
    'laundry_1person': 30000,          # 30,000đ
    'laundry_2person': 40000,          # 40,000đ
    'laundry_3person': 50000,          # 50,000đ
    'laundry_4plus': 60000,            # 60,000đ
    'trash_fee': 0,                    # Tiền rác (mặc định 0)
    'internet_fee': 0,                 # Tiền internet (mặc định 0)
}

# Cấu hình tính toán
CALCULATION = {
    'electricity_price': 3500,
    'water_price': 50000,
    'num_rooms': 7,  # Số phòng
}

# Cấu hình in
PRINTER = {
    'paper_width': 80,  # mm (máy in nhiệt 80mm)
    'font_size': 10,
}

# Cấu hình backup
BACKUP = {
    'auto_backup': True,
    'backup_folder': 'backups',
    'backup_interval': 86400,  # 1 ngày (tính bằng giây)
}

# Cấu hình giao diện
UI = {
    'theme': 'light',
    'font_family': 'Arial',
    'font_size': 10,
}

# Ngôn ngữ
LANGUAGE = 'vi'  # Vietnamese

# Thông báo
MESSAGES = {
    'success_add': '✅ Thêm thành công!',
    'success_update': '✅ Cập nhật thành công!',
    'success_delete': '✅ Xóa thành công!',
    'error_add': '❌ Lỗi khi thêm!',
    'error_update': '❌ Lỗi khi cập nhật!',
    'error_delete': '❌ Lỗi khi xóa!',
    'confirm_delete': '⚠️ Bạn chắc chắn muốn xóa?',
}

# Định dạng ngày tháng
DATE_FORMAT = '%d/%m/%Y'
TIME_FORMAT = '%H:%M:%S'
DATETIME_FORMAT = '%d/%m/%Y %H:%M:%S'

# Các tháng trong năm
MONTHS = {
    1: 'Tháng 1',
    2: 'Tháng 2',
    3: 'Tháng 3',
    4: 'Tháng 4',
    5: 'Tháng 5',
    6: 'Tháng 6',
    7: 'Tháng 7',
    8: 'Tháng 8',
    9: 'Tháng 9',
    10: 'Tháng 10',
    11: 'Tháng 11',
    12: 'Tháng 12',
}
