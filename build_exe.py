"""
Script tạo file EXE bằng PyInstaller.
Chạy: python build_exe.py
"""
import subprocess
import sys
import os


def build_exe():
    """Tạo file EXE từ source code."""
    print("=" * 50)
    print("🔨 Bắt đầu tạo file EXE...")
    print("=" * 50)

    # Kiểm tra PyInstaller
    try:
        import PyInstaller
        print(f"✅ PyInstaller {PyInstaller.__version__} đã cài")
    except ImportError:
        print("❌ Chưa cài PyInstaller!")
        print("Cài bằng lệnh: pip install pyinstaller")
        sys.exit(1)

    # Tên ứng dụng
    app_name = "QuanLyPhongTro"

    # Lệnh PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                    # Đóng gói thành 1 file EXE
        "--windowed",                   # Không hiện console (GUI app)
        f"--name={app_name}",           # Tên file EXE
        "--add-data=database;database", # Thêm thư mục database
        "--add-data=ui;ui",             # Thêm thư mục ui
        "--add-data=utils;utils",       # Thêm thư mục utils
        "--hidden-import=PyQt5",
        "--hidden-import=PyQt5.QtWidgets",
        "--hidden-import=PyQt5.QtCore",
        "--hidden-import=PyQt5.QtGui",
        "--hidden-import=sqlite3",
        "--hidden-import=reportlab",
        "--hidden-import=pandas",
        "--hidden-import=openpyxl",
        "--clean",                      # Xóa cache cũ
        "main.py",                      # File entry point
    ]

    # Thêm icon nếu có
    icon_path = "icon.ico"
    if os.path.exists(icon_path):
        cmd.insert(-1, f"--icon={icon_path}")
        print(f"✅ Sử dụng icon: {icon_path}")

    print(f"\n🚀 Chạy lệnh:\n{' '.join(cmd)}\n")

    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print("\n" + "=" * 50)
        print(f"✅ Tạo EXE thành công!")
        print(f"📁 File EXE nằm trong thư mục: dist/{app_name}.exe")
        print("=" * 50)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Lỗi tạo EXE: {e}")
        sys.exit(1)


if __name__ == "__main__":
    build_exe()
