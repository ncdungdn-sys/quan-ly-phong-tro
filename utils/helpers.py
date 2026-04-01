"""
Các hàm tiện ích - tính toán tiền điện, nước, giặt, format số...
"""
from datetime import datetime
from database import db_manager


def format_currency(amount):
    """Format số tiền theo kiểu Việt Nam (VD: 1.500.000đ)."""
    if amount is None:
        return "0đ"
    return f"{int(amount):,}đ".replace(",", ".")


def format_number(number):
    """Format số với dấu chấm phân cách nghìn."""
    if number is None:
        return "0"
    return f"{int(number):,}".replace(",", ".")


def calculate_electricity(old_reading, new_reading):
    """Tính tiền điện dựa trên số điện."""
    price_per_unit = float(db_manager.get_setting("electricity_price", "3500"))
    units_used = max(0, new_reading - old_reading)
    return units_used * price_per_unit, units_used


def calculate_water(num_people):
    """Tính tiền nước dựa trên số người."""
    price_per_person = float(db_manager.get_setting("water_price_per_person", "50000"))
    return num_people * price_per_person


def calculate_laundry(num_people):
    """Tính tiền giặt dựa trên số người."""
    if num_people <= 0:
        return 0
    elif num_people == 1:
        return float(db_manager.get_setting("laundry_1_person", "30000"))
    elif num_people == 2:
        return float(db_manager.get_setting("laundry_2_person", "40000"))
    elif num_people == 3:
        return float(db_manager.get_setting("laundry_3_person", "50000"))
    else:
        return float(db_manager.get_setting("laundry_4plus_person", "60000"))


def get_laundry_price_text(num_people):
    """Lấy text mô tả giá giặt."""
    price = calculate_laundry(num_people)
    return format_currency(price)


def calculate_room_bill(room_id, month, year):
    """
    Tính toán hóa đơn đầy đủ cho một phòng trong tháng.
    Trả về dict chứa chi tiết từng khoản.
    """
    room = db_manager.get_room_by_id(room_id)
    if not room:
        return None

    residents = db_manager.get_residents_by_room(room_id, active_only=True)
    num_people = len(residents)
    resident_id = residents[0]["id"] if residents else None

    # Tiền phòng
    rent_amount = room["price"]

    # Tiền điện
    elec_reading = db_manager.get_electricity_reading(room_id, month, year)
    electricity_amount = 0
    units_used = 0
    old_reading = 0
    new_reading = 0
    if elec_reading:
        old_reading = elec_reading["old_reading"]
        new_reading = elec_reading["new_reading"]
        electricity_amount, units_used = calculate_electricity(old_reading, new_reading)
    else:
        # Thử lấy số mới nhất từ tháng trước
        last = db_manager.get_last_electricity_reading(room_id, month, year)
        if last:
            old_reading = last["new_reading"]

    # Tiền nước
    water_amount = calculate_water(num_people) if num_people > 0 else 0

    # Tiền giặt
    laundry_record = db_manager.get_laundry_record(room_id, month, year)
    if laundry_record:
        laundry_amount = laundry_record["amount"]
    else:
        laundry_amount = calculate_laundry(num_people) if num_people > 0 else 0

    # Phí rác và internet
    garbage_amount = float(db_manager.get_setting("garbage_fee", "0"))
    internet_amount = float(db_manager.get_setting("internet_fee", "0"))

    # Chi phí phòng do cư dân chịu
    room_expenses = db_manager.get_room_expenses_by_room_month(room_id, month, year)
    room_expense_amount = sum(
        e["amount"] for e in room_expenses if e["paid_by"] == "resident"
    )

    total = (rent_amount + electricity_amount + water_amount + laundry_amount +
             garbage_amount + internet_amount + room_expense_amount)

    return {
        "room_id": room_id,
        "room_number": room["room_number"],
        "resident_id": resident_id,
        "num_people": num_people,
        "month": month,
        "year": year,
        "rent_amount": rent_amount,
        "electricity_amount": electricity_amount,
        "water_amount": water_amount,
        "laundry_amount": laundry_amount,
        "garbage_amount": garbage_amount,
        "internet_amount": internet_amount,
        "room_expense_amount": room_expense_amount,
        "other_amount": 0,
        "total_amount": total,
        "old_reading": old_reading,
        "new_reading": new_reading,
        "units_used": units_used,
        "residents": residents,
    }


def generate_monthly_bills(month, year):
    """Tạo hóa đơn cho tất cả phòng có người ở trong tháng."""
    rooms = db_manager.get_all_rooms()
    generated = []
    for room in rooms:
        if room["status"] == "occupied":
            bill_data = calculate_room_bill(room["id"], month, year)
            if bill_data:
                bill_id = db_manager.save_bill(
                    room["id"],
                    bill_data["resident_id"],
                    month, year,
                    bill_data["rent_amount"],
                    bill_data["electricity_amount"],
                    bill_data["water_amount"],
                    bill_data["laundry_amount"],
                    bill_data["garbage_amount"],
                    bill_data["internet_amount"],
                    bill_data["room_expense_amount"],
                    bill_data["other_amount"],
                )
                generated.append(bill_id)
    return generated


def get_month_name(month):
    """Lấy tên tháng bằng tiếng Việt."""
    months = {
        1: "Tháng 1", 2: "Tháng 2", 3: "Tháng 3",
        4: "Tháng 4", 5: "Tháng 5", 6: "Tháng 6",
        7: "Tháng 7", 8: "Tháng 8", 9: "Tháng 9",
        10: "Tháng 10", 11: "Tháng 11", 12: "Tháng 12",
    }
    return months.get(month, f"Tháng {month}")


def get_current_month_year():
    """Lấy tháng và năm hiện tại."""
    now = datetime.now()
    return now.month, now.year


def parse_date(date_str):
    """Phân tích chuỗi ngày tháng."""
    if not date_str:
        return None
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def format_date(date_str, output_format="%d/%m/%Y"):
    """Format lại ngày tháng."""
    dt = parse_date(date_str)
    if dt:
        return dt.strftime(output_format)
    return date_str or ""
