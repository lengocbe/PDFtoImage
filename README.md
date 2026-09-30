# PDF sang ảnh (Windows)

Ứng dụng Windows độc lập để chuyển từng trang trong một file PDF thành ảnh PNG hoặc JPG.

## Chức năng

- Chỉ nhận file `.pdf`; PDF gốc không bị thay đổi.
- Xuất toàn bộ PDF hoặc nhập các trang cần xuất, ví dụ `1, 3, 5-8`.
- PNG là lựa chọn mặc định; có thể chuyển sang JPG.
- Ảnh được render ở 200 DPI, giữ đúng tỉ lệ/trang PDF.
- Tên ảnh được đánh số liên tiếp theo thứ tự xuất: `trang_001.png`, `trang_002.png`...
- Chọn được thư mục xuất và xem tiến độ cơ bản.

## Cài đặt và chạy

Yêu cầu Python 3.10 trở lên trên Windows.

```powershell
py -m pip install -r requirements.txt
py app.py
```

## Chạy kiểm thử

```powershell
py -m unittest discover -s tests -v
```

## Đóng gói EXE (tùy chọn)

```powershell
py -m pip install pyinstaller
py -m PyInstaller --noconsole --onefile --name PDF_sang_anh app.py
```

File `.exe` sẽ nằm trong thư mục `dist`.
