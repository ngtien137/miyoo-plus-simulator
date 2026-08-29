# 🎮 Miyoo Mini Plus Simulator & MicroSD Studio

![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows)
![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python)
![Qt6](https://img.shields.io/badge/GUI-PyQt6%20%2F%20Qt6-41CD52?logo=qt)
![License](https://img.shields.io/badge/License-MIT-blue)
![Release](https://img.shields.io/badge/Release-Portable%20Standalone%20(No%20Python%20Needed)-success)

Ứng dụng giả lập phần cứng máy chơi game cầm tay **Miyoo Mini Plus** và Studio quản lý, xem trước, khởi tạo thẻ nhớ MicroSD trực tiếp trên máy tính Windows.

---

## 📸 Giao diện Ứng dụng (App Screenshot)

![Miyoo Mini Plus Simulator & Studio Preview](docs/screenshots/app_preview.png)

---

## ✨ Tính Năng Nổi Bật (Key Features)

### 1. 🎮 Giả lập Phần cứng Miyoo Mini Plus 1:1 Pixel-Perfect
* **Màn hình chuẩn phần cứng:** Mô phỏng đúng tỉ lệ 4:3 độ phân giải gốc 640 x 480 IPS của Miyoo Mini Plus.
* **4 Màu vỏ Casing thực tế:** Chuyển đổi linh hoạt giữa các phiên bản màu máy:
  * 🔘 **Retro Grey** (Xám cổ điển Game Boy)
  * ⬛ **Transparent Black** (Đen khói trong suốt)
  * ⚪ **Pure White** (Trắng tinh khôi)
  * 🟣 **Transparent Purple** (Tím Atomic trong suốt)
* **Tương tác phím vật lý:** Hỗ trợ click chuột trực tiếp vào các phím bấm trên thân máy (D-Pad, A/B/X/Y, START, SELECT, MENU) hoặc sử dụng bàn phím máy tính / tay cầm Gamepad.

### 2. 💾 Quản lý Thẻ nhớ & Chẩn đoán Boot Linux Đa Hệ Điều Hành
* **Nhận diện tự động siêu tốc:** Quét thẻ nhớ cắm ngoài qua Windows Kernel API (GetLogicalDrives) chỉ trong 0.01 mili-giây.
* **Phân tích cấu trúc Boot:**
  * ⚡ **Custom OS:** Nhận diện và chạy toàn bộ hệ sinh thái Custom OS từ thẻ nhớ.
  * ⚙️ **Stock OS:** Chế độ hiển thị giao diện xuất xưởng từ chip nhớ NAND Flash.
  * 🔲 **MinUI / Koriki / Batocera / Allium:** Tương thích và kiểm tra file hệ điều hành tương ứng.
  * ⚠️ **Recovery Mode:** Tự động cảnh báo khi thẻ nhớ chưa được cắm hoặc rỗng.

### 3. 🎨 Theme Studio & Xem trước Giao diện Trực quan
* **Đọc trực tiếp từ MicroSD:** Tự động quét toàn bộ thư mục Themes/ của thẻ nhớ đang chọn.
* **Live Theme Preview:** Xem trước ảnh nền (background.png), icon hệ thống, thanh điều hướng, font chữ và bảng màu (Title, Battery, Hint).
* **Trình phát âm thanh (Audio Engine):** Hỗ trợ phát nhạc nền (BGM) và hiệu ứng âm thanh (SFX: Nav, Select, Back) theo từng theme.
* **Xuất Theme 1-Click:** Xuất ngược theme bạn đã chỉnh sửa vào thẻ nhớ MicroSD.

### 4. 🕹️ Quản lý ROM & Trình duyệt Game Đa Hệ Máy
* Tự động duyệt và lập chỉ mục ROM theo từng folder hệ máy: GBA, PS, SFC, FC, NDS, ARCADE, PICO, MD, GBC, GB, NEOGEO, PORTS.
* Hỗ trợ ghim game Yêu thích (**Favorites**) và trình chuyển đổi game nhanh (**Game Switcher**).

### 5. 🛠️ Công cụ Khởi tạo & Định dạng Thẻ nhớ An toàn
* Tự động khởi tạo cấu trúc thư mục chuẩn Miyoo:
  `
  SD_CARD/
  ├── Roms/          (GBA, PS, SFC, FC, NDS, MD, ARCADE...)
  ├── Saves/         (Lưu game & State)
  ├── BIOS/          (BIOS các hệ máy)
  ├── Themes/        (Giao diện tùy biến)
  └── Screenshots/   (Ảnh chụp màn hình)
  `
* **Chế độ bảo vệ dữ liệu:** Tự động sao lưu ROMs, Saves, BIOS cũ sang thư mục an toàn trước khi định dạng thẻ.

---

## 🚀 Hướng Dẫn Sử Dụng (Quick Start)

### Cách 1: Sử dụng Bản Portable (Khuyên dùng - Không cần cài Python)
1. Mở thư mục **windows/**.
2. Click đúp vào file **MiyooPlusSimulator.exe**.
3. Ứng dụng sẽ khởi động ngay lập tức mà không cần cài đặt thêm bất kỳ phần mềm nào.

### Cách 2: Chạy từ Mã Nguồn (Dành cho Lập trình viên)
Yêu cầu: Python 3.10+ trở lên.

`ash
# 1. Cài đặt các thư viện cần thiết
pip install PyQt6 pygame

# 2. Khởi chạy ứng dụng
python run.py
`

---

## ⌨️ Bảng Phím Tắt Điều Khiển (Controls Mapping)

| Phím Bàn Phím | Nút Miyoo Tương Ứng | Chức Năng |
| :--- | :--- | :--- |
| W / A / S / D hoặc Phím Mũi Tên | **D-Pad** | Di chuyển lên / xuống / trái / phải |
| J hoặc Enter | **Nút A** | Chọn / Mở Game / Vào mục |
| K hoặc Escape | **Nút B** | Quay lại / Hủy |
| U | **Nút X** | Đánh dấu Yêu thích / Tùy chọn |
| I | **Nút Y** | Menu phụ |
| M hoặc Space | **Nút MENU** | Mở trình chuyển game nhanh (Game Switcher) |
| Q / E | **L1 / R1** | Chuyển Tab danh mục trước / sau |
| Chuột trái | **Click nút trên thân máy** | Nhấn trực tiếp vào bất kỳ nút nào trên vỏ máy |

---

## 📁 Cấu Trúc Mã Nguồn Dự Án

`
miyoo-plus-simulator/
├── assets/                  # Tài nguyên icons vector, app icons
│   └── icons/
├── docs/                    # Tài liệu và hình ảnh hướng dẫn
│   └── screenshots/
├── simulator/               # Mã nguồn lõi ứng dụng
│   ├── control_deck.py      # Bảng điều khiển Studio bên phải (4 Tabs)
│   ├── handheld_frame.py    # Dựng khung vỏ máy 4 màu và nút bấm vật lý
│   ├── main.py              # Cửa sổ chính và kết nối các thành phần
│   ├── models.py            # Quản lý dữ liệu hệ thống, quét ROMs & Boot loader
│   ├── screen_canvas.py     # Engine vẽ màn hình 640x480 và carousel
│   └── theme_manager.py     # Quản lý nạp theme và audio BGM/SFX
├── tests/                   # Bộ kiểm thử tự động (Regression Tests)
│   └── test_simulator.py
├── tools/                   # Công cụ đóng gói bản Windows Portable
│   ├── build_exe.py
│   └── build_exe.bat
├── windows/                 # Thư mục phát hành Portable chạy ngay (.exe)
│   ├── _internal/           # Thư viện DLL đồ họa và máy ảo nhị phân
│   ├── assets/
│   ├── LICENSE
│   ├── README.md
│   └── MiyooPlusSimulator.exe
├── run.py                   # Điểm khởi chạy chương trình
├── README.md
└── LICENSE
`

---

## 🛠️ Đóng Gói Lại Bản Windows (.exe)

Nếu bạn thực hiện thay đổi trong mã nguồn và muốn đóng gói lại bản Windows Portable:
`ash
python tools/build_exe.py
`
Hoặc click đúp vào file 	ools/build_exe.bat. Kết quả sẽ được cập nhật tự động vào thư mục windows/.

---

## 📄 Bản Quyền (License)

Dự án được phát hành dưới giấy phép mã nguồn mở **MIT License**. Bạn có toàn quyền sử dụng, chỉnh sửa và phân phối tự do.
