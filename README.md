# 🏠 Quản Lý Phòng Trọ

Ứng dụng quản lý phòng trọ đầy đủ tính năng, xây dựng bằng **Python + PyQt5 + SQLite**.

---

## ✨ Tính Năng

### 🏠 Quản Lý Phòng
- 7 phòng trọ với giá khác nhau (có thể chỉnh sửa)
- Theo dõi trạng thái phòng (trống / có người ở)

### 👥 Quản Lý Cư Dân
- Thêm, sửa, xóa cư dân
- Lưu: Họ tên, tuổi, CCCD, SĐT, ghi chú, ngày vào ở
- Ghi nhận trả phòng

### 💰 Tính Tiền Hàng Tháng
- **Tiền phòng:** Giá riêng mỗi phòng
- **Tiền điện:** 3.500đ/số (ghi mốc đầu - mốc cuối)
- **Tiền nước:** 50.000đ/người/tháng
- **Tiền giặt:** 30K-60K tùy số người
- **Tiền rác & Internet:** Có thể bật/tắt, cài giá
- **Chi phí phòng:** Có thể chọn chủ chịu hoặc cư dân chịu

### 📋 Hóa Đơn
- Tự động tạo hóa đơn theo tháng
- Xem chi tiết từng khoản
- Đánh dấu đã thanh toán
- **In hóa đơn PDF A4 hoặc máy in nhiệt 80mm**

### 📊 Báo Cáo
- Báo cáo theo tháng/năm
- Doanh thu, chi phí, lợi nhuận
- Xuất Excel
- Lịch sử giao dịch

### ⚙️ Cài Đặt
- Chỉnh giá phòng riêng từng phòng
- Chỉnh giá điện, nước, giặt, rác, internet

---

## 🚀 Cài Đặt & Chạy

### Yêu Cầu
- Python 3.8+
- pip

### Bước 1: Clone repository
```bash
git clone https://github.com/ncdungdn-sys/quan-ly-phong-tro.git
cd quan-ly-phong-tro
```

### Bước 2: Cài thư viện
```bash
pip install -r requirements.txt
```

### Bước 3: Chạy ứng dụng
```bash
python main.py
```

---

## 📁 Cấu Trúc Project

```
quan-ly-phong-tro/
├── main.py                  # Entry point
├── requirements.txt         # Danh sách thư viện
├── build_exe.py             # Script tạo file EXE
├── phong_tro.db             # Database SQLite (tự tạo lần đầu)
│
├── database/
│   └── db_manager.py        # Quản lý database, CRUD
│
├── ui/
│   ├── main_window.py       # Cửa sổ chính
│   ├── dashboard.py         # Dashboard tổng quan
│   ├── residents_tab.py     # Quản lý cư dân
│   ├── electricity_tab.py   # Ghi số điện
│   ├── laundry_tab.py       # Ghi chép giặt
│   ├── expenses_tab.py      # Quản lý chi phí
│   ├── bills_tab.py         # Hóa đơn
│   ├── reports_tab.py       # Báo cáo
│   └── settings_tab.py      # Cài đặt
│
└── utils/
    ├── helpers.py           # Hàm tiện ích, tính toán
    ├── pdf_generator.py     # Xuất PDF hóa đơn
    └── excel_exporter.py    # Xuất báo cáo Excel
```

---

## 🖨️ Tạo File EXE (Windows)

```bash
python build_exe.py
```
File EXE sẽ nằm trong thư mục `dist/QuanLyPhongTro.exe`

---

## 💾 Backup Dữ Liệu

- **Tự backup thủ công:** Menu → Tệp → Backup dữ liệu
- **Khôi phục:** Menu → Tệp → Khôi phục dữ liệu
- File database: `phong_tro.db` (có thể copy thủ công)

---

## 🛠️ Công Nghệ

| Công nghệ | Mục đích |
|-----------|----------|
| Python 3.8+ | Ngôn ngữ lập trình |
| PyQt5 | Giao diện đồ họa |
| SQLite | Cơ sở dữ liệu |
| reportlab | Xuất PDF hóa đơn |
| pandas + openpyxl | Xuất báo cáo Excel |
| PyInstaller | Đóng gói thành EXE |

---

## 📝 Ghi Chú

- Database tự tạo lần đầu tại `phong_tro.db`
- 7 phòng mặc định: P101, P102, P201, P202, P301, P302, P401
- Giá mặc định có thể thay đổi trong tab **Cài Đặt**
Ứng dụng quản lý phòng trọ
