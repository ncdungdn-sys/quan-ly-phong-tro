"""
Script để build file EXE từ Python code
Sử dụng PyInstaller

Cách dùng:
    python build_exe.py
"""

import os
import sys
import subprocess
import shutil

def build_exe():
    """Build file EXE"""
    print("=" * 60)
    print("🔨 Đang build file EXE...")
    print("=" * 60)
    
    # Tên file EXE
    app_name = "QuanLyPhongTro"
    
    # Lệnh build
    build_command = [
        'pyinstaller',
        '--name=' + app_name,
        '--onefile',  # Gom tất cả vào 1 file
        '--windowed',  # Không hiển thị console
        '--icon=icon.ico',  # Icon (nếu có)
        '--add-data=config.py:.',
        'main.py'
    ]
    
    try:
        # Chạy PyInstaller
        subprocess.run(build_command, check=True)
        print("\n✅ Build thành công!")
        print(f"\n📁 File EXE nằm tại: dist/{app_name}.exe")
        print("\n💡 Hướng dẫn:")
        print("   1. Copy file exe ra folder riêng")
        print("   2. Chạy file exe (không cần Python)")
        print("   3. Database sẽ tự tạo ở cùng folder với exe")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Lỗi khi build: {e}")
        print("\n🔧 Cài đặt PyInstaller:")
        print("   pip install pyinstaller")
        return False
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        return False
    
    return True


def cleanup():
    """Dọn dẹp file tạm"""
    print("\n🧹 Dọn dẹp file tạm...")
    
    # Xóa folder build
    if os.path.exists('build'):
        shutil.rmtree('build')
        print("   ✅ Xóa folder build")
    
    # Xóa file spec
    for file in os.listdir('.'):
        if file.endswith('.spec'):
            os.remove(file)
            print(f"   ✅ Xóa file {file}")


def main():
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "QUẢN LÝ PHÒNG TRỌ - BUILD EXE" + " " * 14 + "║")
    print("╚" + "=" * 58 + "╝")
    
    # Kiểm tra PyInstaller
    try:
        import PyInstaller
    except ImportError:
        print("\n⚠️  PyInstaller chưa được cài đặt!")
        print("🔧 Cài đặt bằng lệnh:")
        print("   pip install pyinstaller")
        return
    
    # Build
    if build_exe():
        cleanup()
        print("\n" + "=" * 60)
        print("🎉 Hoàn thành!")
        print("=" * 60 + "\n")
    else:
        print("\n❌ Build thất bại\n")


if __name__ == "__main__":
    main()
