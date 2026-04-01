from datetime import datetime, date, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
import os

class PDFGenerator:
    """Tạo file PDF cho hóa đơn"""
    
    @staticmethod
    def create_bill_pdf(bill_data, output_path='bills'):
        """Tạo PDF hóa đơn"""
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        
        filename = f"{output_path}/bill_{bill_data['bill_id']}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=A4)
        elements = []
        
        # Tiêu đề
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=6,
            alignment=1  # Center
        )
        
        title = Paragraph("HÓA ĐƠN HÀNG THÁNG", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.3*cm))
        
        # Thông tin hóa đơn
        info_data = [
            ['Mã Hóa Đơn:', f"#{bill_data['bill_id']}"],
            ['Phòng:', bill_data['room_name']],
            ['Cư Dân:', bill_data['resident_name']],
            ['Tháng:', bill_data['month']],
            ['Ngày Lập:', datetime.now().strftime('%d/%m/%Y')],
        ]
        
        info_table = Table(info_data, colWidths=[3*cm, 10*cm])
        info_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8E8E8')),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.5*cm))
        
        # Bảng chi tiết
        detail_data = [
            ['Hạng Mục', 'Số Tiền (VND)'],
        ]
        
        if bill_data.get('room_fee'):
            detail_data.append(['Tiền Phòng', f"{bill_data['room_fee']:,.0f}"])
        if bill_data.get('electricity_fee'):
            detail_data.append(['Tiền Điện', f"{bill_data['electricity_fee']:,.0f}"])
        if bill_data.get('water_fee'):
            detail_data.append(['Tiền Nước', f"{bill_data['water_fee']:,.0f}"])
        if bill_data.get('laundry_fee'):
            detail_data.append(['Tiền Giặt', f"{bill_data['laundry_fee']:,.0f}"])
        if bill_data.get('other_fees'):
            detail_data.append(['Chi Phí Khác', f"{bill_data['other_fees']:,.0f}"])
        
        detail_data.append(['TỔNG CỘNG', f"{bill_data['total_amount']:,.0f}"])
        
        detail_table = Table(detail_data, colWidths=[10*cm, 5*cm])
        detail_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
            ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 11),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#D9E1F2')),
            ('FONT', (0, -1), (-1, -1), 'Helvetica-Bold', 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F2F2F2')]),
        ]))
        elements.append(detail_table)
        elements.append(Spacer(1, 1*cm))
        
        # Trạng thái thanh toán
        status = "✅ ĐÃ THANH TOÁN" if bill_data.get('paid') else "⏳ CHƯA THANH TOÁN"
        status_style = ParagraphStyle(
            'Status',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#00B050') if bill_data.get('paid') else colors.HexColor('#FF0000'),
            spaceAfter=12,
            alignment=1
        )
        elements.append(Paragraph(status, status_style))
        
        # Lưu PDF
        doc.build(elements)
        return filename


class Calculator:
    """Tính toán các khoản phí"""
    
    @staticmethod
    def calculate_electricity_usage(old_reading, new_reading):
        """Tính lượng điện sử dụng"""
        return max(0, new_reading - old_reading)
    
    @staticmethod
    def calculate_electricity_fee(usage, price_per_unit=3500):
        """Tính tiền điện"""
        return usage * price_per_unit
    
    @staticmethod
    def calculate_water_fee(num_people, price_per_person=50000):
        """Tính tiền nước"""
        return num_people * price_per_person
    
    @staticmethod
    def calculate_laundry_fee(num_people):
        """Tính tiền giặt theo số người"""
        if num_people == 1:
            return 30000
        elif num_people == 2:
            return 40000
        elif num_people == 3:
            return 50000
        else:  # 4+
            return 60000
    
    @staticmethod
    def calculate_total_bill(room_fee, electricity_fee, water_fee, laundry_fee, other_fees=0):
        """Tính tổng hóa đơn"""
        return room_fee + electricity_fee + water_fee + laundry_fee + other_fees


class DateHelper:
    """Hỗ trợ xử lý ngày tháng"""
    
    @staticmethod
    def get_current_month():
        """Lấy tháng hiện tại"""
        return datetime.now().strftime('%Y-%m')
    
    @staticmethod
    def get_month_str(date_obj):
        """Lấy chuỗi tháng từ date object"""
        if isinstance(date_obj, str):
            return date_obj
        return date_obj.strftime('%Y-%m')
    
    @staticmethod
    def get_month_year(date_obj):
        """Lấy tháng/năm"""
        if isinstance(date_obj, str):
            return date_obj
        return date_obj.strftime('%m/%Y')
    
    @staticmethod
    def get_date_range(month):
        """Lấy ngày bắt đầu và kết thúc của tháng"""
        try:
            year, month_num = map(int, month.split('-'))
        except:
            today = datetime.now()
            year = today.year
            month_num = today.month
        
        first_day = date(year, month_num, 1)
        if month_num == 12:
            last_day = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(year, month_num + 1, 1) - timedelta(days=1)
        
        return first_day, last_day
    
    @staticmethod
    def is_bill_due(check_in_day, current_day=None):
        """Kiểm tra có phải ngày thu tiền không"""
        if current_day is None:
            current_day = datetime.now().day
        
        return current_day == check_in_day


class FormatHelper:
    """Hỗ trợ định dạng dữ liệu"""
    
    @staticmethod
    def format_currency(amount):
        """Định dạng tiền tệ"""
        return f"{amount:,.0f} ₫"
    
    @staticmethod
    def format_date(date_obj, format_str='%d/%m/%Y'):
        """Định dạng ngày"""
        if isinstance(date_obj, str):
            try:
                date_obj = datetime.strptime(date_obj, '%Y-%m-%d')
            except:
                return date_obj
        return date_obj.strftime(format_str)
    
    @staticmethod
    def format_phone(phone):
        """Định dạng số điện thoại"""
        if not phone:
            return ''
        phone = phone.replace(' ', '').replace('-', '')
        if len(phone) == 10:
            return f"{phone[:3]} {phone[3:6]} {phone[6:]}"
        return phone
    
    @staticmethod
    def format_percentage(value, decimal=2):
        """Định dạng phần trăm"""
        return f"{value:.{decimal}f}%"


class Validator:
    """Xác thực dữ liệu"""
    
    @staticmethod
    def is_valid_phone(phone):
        """Kiểm tra số điện thoại hợp lệ"""
        phone = phone.replace(' ', '').replace('-', '')
        return len(phone) >= 9 and phone.isdigit()
    
    @staticmethod
    def is_valid_cccd(cccd):
        """Kiểm tra CCCD hợp lệ"""
        cccd = cccd.replace(' ', '')
        return len(cccd) in [9, 12] and cccd.isdigit()
    
    @staticmethod
    def is_valid_email(email):
        """Kiểm tra email hợp lệ"""
        return '@' in email and '.' in email
    
    @staticmethod
    def is_valid_price(price):
        """Kiểm tra giá hợp lệ"""
        try:
            p = float(price)
            return p >= 0
        except:
            return False
    
    @staticmethod
    def is_valid_age(age):
        """Kiểm tra tuổi hợp lệ"""
        try:
            a = int(age)
            return 1 <= a <= 150
        except:
            return False


class Logger:
    """Ghi log hoạt động"""
    
    @staticmethod
    def log_action(action, details, log_file='app.log'):
        """Ghi log hành động"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {action}: {details}\n"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_message)
    
    @staticmethod
    def log_error(error, log_file='errors.log'):
        """Ghi log lỗi"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] ERROR: {str(error)}\n"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_message)
