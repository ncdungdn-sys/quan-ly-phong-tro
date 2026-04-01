# 🏠 Ứng Dụng Quản Lý Phòng Trọ

Ứng dụng quản lý phòng trọ toàn diện với 7 phòng, hỗ trợ quản lý cư dân, tính toán tiền điện nước giặt, quản lý chi phí, và xuất hóa đơn in nhiệt.

## ✨ Tính Năng Chính

### 1. 👥 Quản Lý Cư Dân
- Thêm, sửa, xóa thông tin cư dân
- Lưu trữ: Tên, tuổi, CCCD, SĐT, ghi chú, ngày vào ở
- Theo dõi trạng thái phòng (trống/đầy)

### 2. 💰 Tính Toán Tiền Hàng Tháng

#### Tiền Phòng
- Giá mỗi phòng khác nhau (có thể chỉnh sửa)
- Thu tiền theo ngày vào ở (VD: vào ngày 10 → thu tiền ngày 10 hàng tháng)

#### Tiền Điện
- **3,500đ/1 số điện**
- Tính theo mốc số (mốc cũ - mốc mới = số dùng)
- Ghi mốc từng phòng theo từng tháng

#### Tiền Nước
- **50,000đ/1 người/1 tháng**
- Tính dựa vào số người trong phòng

#### Tiền Giặt
- **1 người: 30,000đ**
- **2 người: 40,000đ**
- **3 người: 50,000đ**
- **4+ người: 60,000đ**

#### Dịch Vụ Khác (Có thể bật/tắt)
- Tiền rác (mặc định 0)
- Tiền internet (mặc định 0)
- Có thể thêm dịch vụ mới

### 3. 📊 Quản Lý Chi Phí

#### Chi Phí Chung
- Sửa chữa chung (mái tôn, tường, v.v.)
- Bảo trì, vệ sinh toàn bộ nhà

#### Chi Phí Phát Sinh Theo Phòng
- Sửa điều hòa, thay bóng đèn, v.v.
- Lựa chọn: Thu từ cư dân hoặc tôi chịu
- Nếu thu từ cư dân → Cộng vào hóa đơn

### 4. 📋 Hóa Đơn & Báo Cáo

#### Hóa Đơn Hàng Tháng
- Tự động tạo theo ngày vào ở
- Bao gồm: Tiền phòng + Điện + Nước + Giặt + Chi phí phát sinh
- Tính lũy kế, trạng thái thanh toán

#### Báo Cáo Lợi Nhuận
- **Tổng doanh thu** = Tiền từ cư dân + Chi phí phòng (cư dân chịu)
- **Tổng chi phí** = Chi phí chung + Chi phí phòng (tôi chịu)
- **Lợi nhuận** = Doanh thu - Chi phí
- Xem theo tháng/năm

### 5. 🖨️ In Hóa Đơn
- Máy in nhiệt 80mm
- In bill trực tiếp hoặc lưu PDF
- Bill hiển thị: Phòng, Cư dân, Chi tiết tiền, Tổng cộng

### 6. 📱 Giao Diện PyQt5

**Dashboard:**
- Tổng phòng, phòng trống, tổng cư dân, doanh thu, chi phí, lợi nhuận
- Menu chính: Cư dân, Hóa đơn, Điện, Nước, Giặt, Chi phí, Báo cáo, In

**Các Mục Quản Lý:**
- ✅ Quản lý cư dân (CRUD)
- ✅ Ghi mốc số điện
- ✅ Ghi chép giặt
- ✅ Quản lý chi phí (chung + phòng)
- ✅ Lịch thu tiền (calendar view)
- ✅ Báo cáo thống kê
- ✅ Cài đặt giá cả

## 🛠️ Công Nghệ Sử Dụng

| Thành Phần | Công Nghệ |
|-----------|----------|
| **Frontend** | PyQt5 (GUI) |
| **Backend** | Python 3.8+ |
| **Database** | SQLite |
| **Xuất Excel** | pandas, openpyxl |
| **In hóa đơn** | reportlab (PDF) |
| **Đóng gói** | PyInstaller (tạo file EXE) |

## 📥 Cài Đặt

### Yêu Cầu
- Python 3.8 trở lên
- pip (Python package manager)

### Bước 1: Clone Repository
```bash
git clone https://github.com/ncdungdn-sys/quan-ly-phong-tro.git
cd quan-ly-phong-tro
