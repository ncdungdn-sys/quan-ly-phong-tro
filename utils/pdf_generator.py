"""
Xuất hóa đơn PDF - hỗ trợ máy in nhiệt 80mm và PDF thông thường.
"""
import os
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase import pdfmetrics
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from utils.helpers import format_currency, format_date, get_month_name


def _register_font():
    """Đăng ký font hỗ trợ tiếng Việt nếu có."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        os.path.join(os.path.dirname(__file__), "fonts", "DejaVuSans.ttf"),
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("ViFont", path))
                return "ViFont"
            except Exception:
                continue
    return "Helvetica"


def generate_bill_pdf(bill_data, residents, output_path=None):
    """
    Tạo hóa đơn PDF từ dữ liệu hóa đơn.

    Args:
        bill_data: dict chứa thông tin hóa đơn
        residents: list cư dân trong phòng
        output_path: đường dẫn file xuất, nếu None thì tạo tự động

    Returns:
        str: đường dẫn file PDF đã tạo
    """
    if not REPORTLAB_AVAILABLE:
        raise ImportError("Cần cài reportlab: pip install reportlab")

    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        room_num = bill_data.get("room_number", "P000")
        output_path = os.path.join(
            os.path.expanduser("~"),
            f"HoaDon_{room_num}_{bill_data.get('month', 0):02d}_{bill_data.get('year', 0)}_{timestamp}.pdf"
        )

    font_name = _register_font()

    # Tạo PDF A4
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontName=font_name,
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=12,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    normal_style = ParagraphStyle(
        "Normal",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=10,
        spaceAfter=2,
    )

    elements = []

    # Tiêu đề
    elements.append(Paragraph("NHÀ TRỌ", title_style))
    elements.append(Paragraph(
        f"HÓA ĐƠN THÁNG {bill_data.get('month', 0):02d}/{bill_data.get('year', 0)}",
        heading_style
    ))
    elements.append(Spacer(1, 5 * mm))

    # Thông tin phòng
    room_info = f"Phòng: <b>{bill_data.get('room_number', '')}</b>"
    elements.append(Paragraph(room_info, normal_style))

    # Thông tin cư dân
    if residents:
        names = ", ".join(r.get("full_name", "") for r in residents)
        elements.append(Paragraph(f"Cư dân: {names}", normal_style))

    elements.append(Paragraph(
        f"Ngày in: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        normal_style
    ))
    elements.append(Spacer(1, 5 * mm))

    # Bảng chi tiết
    table_data = [
        ["Khoản", "Chi tiết", "Số tiền"],
        ["Tiền phòng", "", format_currency(bill_data.get("rent_amount", 0))],
    ]

    # Tiền điện
    units = bill_data.get("units_used", 0)
    old_r = bill_data.get("old_reading", 0)
    new_r = bill_data.get("new_reading", 0)
    elec_detail = f"{old_r:.0f} → {new_r:.0f} ({units:.0f} số)"
    table_data.append(["Tiền điện", elec_detail, format_currency(bill_data.get("electricity_amount", 0))])

    # Tiền nước
    num_people = bill_data.get("num_people", 0)
    water_detail = f"{num_people} người × 50,000đ"
    table_data.append(["Tiền nước", water_detail, format_currency(bill_data.get("water_amount", 0))])

    # Tiền giặt
    table_data.append([
        "Tiền giặt",
        f"{num_people} người",
        format_currency(bill_data.get("laundry_amount", 0))
    ])

    if bill_data.get("garbage_amount", 0) > 0:
        table_data.append(["Tiền rác", "", format_currency(bill_data.get("garbage_amount", 0))])

    if bill_data.get("internet_amount", 0) > 0:
        table_data.append(["Tiền internet", "", format_currency(bill_data.get("internet_amount", 0))])

    if bill_data.get("room_expense_amount", 0) > 0:
        table_data.append([
            "Chi phí phòng",
            "",
            format_currency(bill_data.get("room_expense_amount", 0))
        ])

    if bill_data.get("other_amount", 0) > 0:
        table_data.append(["Khác", "", format_currency(bill_data.get("other_amount", 0))])

    # Tổng cộng
    table_data.append(["TỔNG CỘNG", "", format_currency(bill_data.get("total_amount", 0))])

    table = Table(table_data, colWidths=[50 * mm, 80 * mm, 40 * mm])
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (2, 0), (2, -1), "RIGHT"),
        ("ALIGN", (0, 0), (1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), font_name),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey),
        ("FONTNAME", (0, -1), (-1, -1), font_name),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.lightyellow]),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 10 * mm))

    # Chân trang
    elements.append(Paragraph("Cảm ơn bạn đã sử dụng dịch vụ!", heading_style))
    elements.append(Paragraph("Vui lòng thanh toán đúng hạn.", normal_style))

    doc.build(elements)
    return output_path


def generate_thermal_bill(bill_data, residents, output_path=None):
    """
    Tạo hóa đơn dạng máy in nhiệt 80mm (PDF khổ hẹp).

    Args:
        bill_data: dict chứa thông tin hóa đơn
        residents: list cư dân trong phòng
        output_path: đường dẫn file xuất

    Returns:
        str: đường dẫn file PDF đã tạo
    """
    if not REPORTLAB_AVAILABLE:
        raise ImportError("Cần cài reportlab: pip install reportlab")

    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        room_num = bill_data.get("room_number", "P000")
        output_path = os.path.join(
            os.path.expanduser("~"),
            f"Bill_Thermal_{room_num}_{bill_data.get('month', 0):02d}_{bill_data.get('year', 0)}_{timestamp}.pdf"
        )

    font_name = _register_font()

    # Khổ in nhiệt 80mm
    thermal_width = 80 * mm
    thermal_height = 200 * mm

    c = canvas.Canvas(output_path, pagesize=(thermal_width, thermal_height))
    c.setFont(font_name, 12)

    y = thermal_height - 15 * mm
    line_height = 5 * mm
    left_margin = 3 * mm
    right_margin = thermal_width - 3 * mm
    content_width = thermal_width - 6 * mm

    def draw_line(text, x=left_margin, size=10, bold=False):
        nonlocal y
        if bold:
            c.setFont(font_name, size)
        else:
            c.setFont(font_name, size)
        c.drawString(x, y, text)
        y -= line_height

    def draw_separator():
        nonlocal y
        c.line(left_margin, y + 2 * mm, right_margin, y + 2 * mm)
        y -= 2 * mm

    def draw_row(label, value, size=9):
        nonlocal y
        c.setFont(font_name, size)
        c.drawString(left_margin, y, label)
        c.drawRightString(right_margin, y, value)
        y -= line_height

    # Tiêu đề
    c.setFont(font_name, 13)
    text_width = c.stringWidth("NHA TRO", font_name, 13)
    c.drawString((thermal_width - text_width) / 2, y, "NHA TRO")
    y -= line_height

    c.setFont(font_name, 10)
    month_text = f"HOA DON T{bill_data.get('month', 0):02d}/{bill_data.get('year', 0)}"
    text_width = c.stringWidth(month_text, font_name, 10)
    c.drawString((thermal_width - text_width) / 2, y, month_text)
    y -= line_height

    draw_separator()

    draw_row("Phong:", bill_data.get("room_number", ""))
    if residents:
        names = ", ".join(r.get("full_name", "") for r in residents[:2])
        if len(names) > 25:
            names = names[:22] + "..."
        draw_row("Cu dan:", names)

    draw_separator()

    draw_row("Tien phong:", format_currency(bill_data.get("rent_amount", 0)))

    # Điện
    units = bill_data.get("units_used", 0)
    old_r = bill_data.get("old_reading", 0)
    new_r = bill_data.get("new_reading", 0)
    draw_row(f"Dien ({old_r:.0f}->{new_r:.0f}):", format_currency(bill_data.get("electricity_amount", 0)))

    # Nước
    draw_row(f"Nuoc ({bill_data.get('num_people', 0)} nguoi):",
             format_currency(bill_data.get("water_amount", 0)))

    # Giặt
    draw_row(f"Giat ({bill_data.get('num_people', 0)} nguoi):",
             format_currency(bill_data.get("laundry_amount", 0)))

    if bill_data.get("garbage_amount", 0) > 0:
        draw_row("Rac:", format_currency(bill_data.get("garbage_amount", 0)))

    if bill_data.get("internet_amount", 0) > 0:
        draw_row("Internet:", format_currency(bill_data.get("internet_amount", 0)))

    if bill_data.get("room_expense_amount", 0) > 0:
        draw_row("Chi phi phong:", format_currency(bill_data.get("room_expense_amount", 0)))

    draw_separator()

    c.setFont(font_name, 11)
    c.drawString(left_margin, y, "TONG CONG:")
    c.drawRightString(right_margin, y, format_currency(bill_data.get("total_amount", 0)))
    y -= line_height

    draw_separator()

    c.setFont(font_name, 9)
    thanks_text = "Cam on! Vui long thanh toan dung han."
    text_width = c.stringWidth(thanks_text, font_name, 9)
    c.drawString((thermal_width - text_width) / 2, y, thanks_text)
    y -= line_height

    date_text = f"In: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    text_width = c.stringWidth(date_text, font_name, 9)
    c.drawString((thermal_width - text_width) / 2, y, date_text)

    c.save()
    return output_path
