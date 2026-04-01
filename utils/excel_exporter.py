"""
Xuất báo cáo Excel sử dụng pandas/openpyxl.
"""
import os
from datetime import datetime

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

from utils.helpers import format_currency, get_month_name
from database import db_manager


def export_monthly_report(month, year, output_path=None):
    """
    Xuất báo cáo tháng ra file Excel.

    Args:
        month: Tháng
        year: Năm
        output_path: Đường dẫn file xuất

    Returns:
        str: Đường dẫn file Excel đã tạo
    """
    if not PANDAS_AVAILABLE:
        raise ImportError("Cần cài pandas: pip install pandas openpyxl")

    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(
            os.path.expanduser("~"),
            f"BaoCao_T{month:02d}_{year}_{timestamp}.xlsx"
        )

    bills = db_manager.get_bills_by_month(month, year)
    expenses = db_manager.get_expenses_by_month(month, year)
    room_expenses = db_manager.get_room_expenses_by_month(month, year)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        # Sheet 1: Hóa đơn
        if bills:
            bill_df = pd.DataFrame(bills)
            bill_columns = {
                "room_number": "Phòng",
                "month": "Tháng",
                "year": "Năm",
                "rent_amount": "Tiền phòng",
                "electricity_amount": "Tiền điện",
                "water_amount": "Tiền nước",
                "laundry_amount": "Tiền giặt",
                "garbage_amount": "Tiền rác",
                "internet_amount": "Tiền internet",
                "room_expense_amount": "Chi phí phòng",
                "other_amount": "Khác",
                "total_amount": "Tổng cộng",
                "paid_amount": "Đã thanh toán",
                "status": "Trạng thái",
            }
            display_cols = [c for c in bill_columns if c in bill_df.columns]
            bill_df = bill_df[display_cols].rename(columns=bill_columns)
            bill_df["Trạng thái"] = bill_df["Trạng thái"].map(
                {"paid": "Đã thanh toán", "unpaid": "Chưa thanh toán", "partial": "Thanh toán một phần"}
            ).fillna("Chưa thanh toán")
            bill_df.to_excel(writer, sheet_name="Hóa đơn", index=False)

        # Sheet 2: Chi phí chung
        if expenses:
            expense_df = pd.DataFrame(expenses)
            expense_columns = {
                "description": "Mô tả",
                "amount": "Số tiền",
                "category": "Loại",
                "created_at": "Ngày tạo",
            }
            display_cols = [c for c in expense_columns if c in expense_df.columns]
            expense_df = expense_df[display_cols].rename(columns=expense_columns)
            expense_df.to_excel(writer, sheet_name="Chi phí chung", index=False)

        # Sheet 3: Chi phí phòng
        if room_expenses:
            room_exp_df = pd.DataFrame(room_expenses)
            room_exp_columns = {
                "room_number": "Phòng",
                "description": "Mô tả",
                "amount": "Số tiền",
                "paid_by": "Người chịu",
                "created_at": "Ngày tạo",
            }
            display_cols = [c for c in room_exp_columns if c in room_exp_df.columns]
            room_exp_df = room_exp_df[display_cols].rename(columns=room_exp_columns)
            room_exp_df["Người chịu"] = room_exp_df["Người chịu"].map(
                {"owner": "Chủ nhà", "resident": "Cư dân"}
            ).fillna("Chủ nhà")
            room_exp_df.to_excel(writer, sheet_name="Chi phí phòng", index=False)

        # Sheet 4: Tổng kết
        summary = db_manager.get_monthly_summary(month, year)
        summary_data = {
            "Chỉ tiêu": [
                "Tháng",
                "Tổng doanh thu",
                "Đã thu",
                "Chi phí chung",
                "Chi phí phòng (chủ chịu)",
                "Tổng chi phí",
                "Lợi nhuận",
            ],
            "Giá trị": [
                f"Tháng {month:02d}/{year}",
                summary["total_revenue"],
                summary["paid_revenue"],
                summary["total_expenses"],
                summary["owner_expenses"],
                summary["total_cost"],
                summary["profit"],
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name="Tổng kết", index=False)

    return output_path


def export_yearly_report(year, output_path=None):
    """
    Xuất báo cáo năm ra file Excel.

    Args:
        year: Năm
        output_path: Đường dẫn file xuất

    Returns:
        str: Đường dẫn file Excel đã tạo
    """
    if not PANDAS_AVAILABLE:
        raise ImportError("Cần cài pandas: pip install pandas openpyxl")

    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(
            os.path.expanduser("~"),
            f"BaoCao_Nam_{year}_{timestamp}.xlsx"
        )

    yearly_data = db_manager.get_yearly_summary(year)

    rows = []
    for m in yearly_data:
        rows.append({
            "Tháng": f"Tháng {m['month']:02d}/{year}",
            "Doanh thu": m["total_revenue"],
            "Đã thu": m["paid_revenue"],
            "Chi phí": m["total_cost"],
            "Lợi nhuận": m["profit"],
        })

    df = pd.DataFrame(rows)

    # Thêm dòng tổng
    total_row = {
        "Tháng": "TỔNG CỘNG",
        "Doanh thu": df["Doanh thu"].sum(),
        "Đã thu": df["Đã thu"].sum(),
        "Chi phí": df["Chi phí"].sum(),
        "Lợi nhuận": df["Lợi nhuận"].sum(),
    }
    df = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=f"Báo cáo năm {year}", index=False)

    return output_path


def export_residents_report(output_path=None):
    """Xuất danh sách cư dân ra file Excel."""
    if not PANDAS_AVAILABLE:
        raise ImportError("Cần cài pandas: pip install pandas openpyxl")

    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(
            os.path.expanduser("~"),
            f"DanhSachCuDan_{timestamp}.xlsx"
        )

    residents = db_manager.get_all_residents(active_only=False)

    if residents:
        df = pd.DataFrame(residents)
        columns = {
            "room_number": "Phòng",
            "full_name": "Họ tên",
            "age": "Tuổi",
            "id_card": "CCCD",
            "phone": "SĐT",
            "check_in_date": "Ngày vào",
            "check_out_date": "Ngày ra",
            "notes": "Ghi chú",
            "is_active": "Đang ở",
        }
        display_cols = [c for c in columns if c in df.columns]
        df = df[display_cols].rename(columns=columns)
        df["Đang ở"] = df["Đang ở"].map({1: "Có", 0: "Không"})
    else:
        df = pd.DataFrame(columns=["Phòng", "Họ tên", "Tuổi", "CCCD", "SĐT",
                                    "Ngày vào", "Ngày ra", "Ghi chú", "Đang ở"])

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Cư dân", index=False)

    return output_path
