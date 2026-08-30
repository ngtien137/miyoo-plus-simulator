# Internationalization (i18n) engine for Miyoo Plus Simulator
# Supports EN (English - Default) and VI (Tiếng Việt)

import os
import json

DEFAULT_LANG = "en"
CURRENT_LANG = DEFAULT_LANG
_LISTENERS = []

TRANSLATIONS = {
    "en": {
        # App & Window
        "app_title": "Miyoo Mini Plus Studio & Simulator",
        "app_header": "🎮 Miyoo Mini Plus Studio & Simulator",
        "lang_label": "🌐 Language:",
        
        # Tabs
        "tab_boot": "💾 MicroSD & Boot",
        "tab_theme": "🎨 Themes & UI",
        "tab_tweaks": "🕹️ Miyoo Tweaks",
        "tab_controls": "⌨️ Controls",

        # Tab 1: Source & Target
        "grp_source": "1. OS Source Payload (Live Preview Source)",
        "btn_browse_src": "📁 Browse Source...",
        "btn_refresh_src": "🔄",
        "hint_src": "💡 The virtual Miyoo console on the left is previewing directly from this Source folder.",
        "src_opt_kayzit": "⚡ Kayzit OS Payload (kayzit-os/payload)",
        "src_opt_workspace": "Virtual SD (Project Workspace)",
        "src_opt_custom": "Custom Payload Folder",
        "src_prefix": "📁 Source: ",

        "grp_target": "2. Target MicroSD Drive (Format & Deployment Destination)",
        "btn_browse_tgt": "📁 Browse Target...",
        "btn_refresh_tgt": "🔄",
        "tgt_tag_sd": " [MicroSD Card]",
        "tgt_tag_miyoo": " [Miyoo MicroSD]",
        "tgt_tag_drive": " [Drive]",
        "tgt_virtual_export": "📁 Virtual SD Export Folder (virtual_sd_export)",
        "tgt_prefix": "📁 Target: ",
        "tgt_info_free": "💾 Free space: {free:.1f} GB / {total:.1f} GB ({path})",
        "tgt_info_missing": "📁 Directory not yet created (will auto-create on deploy): {path}",

        "grp_diag": "3. Source Bootloader Diagnostics (Preview)",
        "btn_reboot": "🔄 Re-Check & Reboot Simulator",
        "boot_custom": "⚡ BOOT MODE: CUSTOM OS (MICROSD ACTIVE)",
        "boot_stock": "⚙️ BOOT MODE: STOCK OS (NAND FACTORY)",
        "boot_nosd": "⚠️ BOOT MODE: NO SD CARD INSERTED",
        "diag_source_path": "<b>Source Payload Path:</b> <code>{path}</code><br><br>",
        "diag_header": "<b>Boot Diagnostics:</b><br>",
        "diag_kernel": "• <b>Linux Kernel:</b> 🟢 Initialized (NAND Flash)<br>",
        "diag_tmp_update": "• <b>.tmp_update/ :</b> {stat}<br>",
        "diag_payload": "• <b>OS Payload/ :</b> {stat}<br>",
        "diag_themes": "• <b>Themes/ :</b> {stat}<br>",
        "diag_roms": "• <b>Roms/ :</b> {stat}<br><br>",
        "diag_decision": "<b>Kernel Decision:</b><br>{msg}",
        "stat_found_installed": "🟢 Found (Installed)",
        "stat_found_daemons": "🟢 Found (MainUI & Daemons)",
        "stat_found_themes": "🟢 Found ({count} themes)",
        "stat_found_roms": "🟢 Found ({count} ROMs indexed)",
        "stat_missing": "🔴 Missing",
        "stat_none": "⚪ None",

        "grp_deploy": "4. MicroSD Setup & Deployment Tools",
        "btn_deploy": "🚀 Copy & Format MicroSD (Source ➔ Target)",
        "btn_export_theme": "📂 Export Active Theme to Target (Themes/)",

        # Deployment Dialog
        "deploy_title": "🛠️ Format & Copy OS to MicroSD Card",
        "deploy_header": "📦 Deploy & Copy Operating System to MicroSD",
        "deploy_source_box": "📥 <b>Source Directory (Previewing):</b><br><code style='color: #00f0ff; font-size: 12px;'>{path}</code>",
        "deploy_target_box": "📤 <b>Target MicroSD / Folder (Destination):</b><br><code style='color: #34c759; font-size: 12px;'>{path}</code>",
        "deploy_grp_mode": "Select Format / Deployment Mode",
        "deploy_mode_preserve": "🛡️ Custom Format (Preserve existing ROMs, Saves, BIOS on Target)",
        "deploy_mode_wipe": "⚠️ Clean Format (Wipe 100% of Target & Fresh Install)",
        "deploy_mode_update": "⚡ Quick Update (Overwrite OS files only, keep all other files)",
        "deploy_grp_list": "Data on Target Card to be Preserved:",
        "deploy_btn_sel_all": "✓ Select All",
        "deploy_btn_desel": "✗ Deselect All",
        "deploy_no_data": "⚪ No existing ROMs/Saves found on target card",
        "deploy_btn_cancel": "❌ Cancel",
        "deploy_btn_start": "🚀 Start Copy & Deployment",
        "deploy_confirm_title": "Confirm Deployment & Copy",
        "deploy_confirm_msg": "Are you sure you want to copy from Source:\n{src}\n\nTo Target:\n{tgt}?\n\n• Mode: {mode}\n• Items preserved: {count} items",
        "deploy_mode_str_preserve": "Preserve selected ROMs/Saves",
        "deploy_mode_str_wipe": "WIPE 100% CLEAN",
        "deploy_mode_str_update": "Quick OS Update",
        "deploy_success_title": "Deployment Successful!",
        "deploy_success_msg": "🎉 Operating system has been copied successfully to:\n{path}!\n\nYour MicroSD card is ready to plug into the Miyoo Mini Plus.",
        "deploy_error_title": "Deployment Error",
        "deploy_error_msg": "An error occurred during deployment:\n{msg}",

        # Progress Strings
        "prog_backup": "📦 Temporarily backing up ROMs, Saves & BIOS on target...",
        "prog_clean_wipe": "🧹 Wiping and cleaning target card completely...",
        "prog_clean_sys": "🧹 Cleaning legacy OS system files on target card...",
        "prog_copying": "📥 Copying operating system from Source to Target...",
        "prog_copy_item": "📂 Copying: {item}...",
        "prog_hierarchy": "📁 Creating standard folders (Roms, Saves, BIOS, Themes)...",
        "prog_restore": "🔄 Restoring preserved ROMs, Saves & BIOS...",
        "prog_done": "✅ Format and deployment completed successfully!",

        # Tab 2: Theme Studio
        "grp_theme_select": "1. Theme Selector",
        "lbl_theme_preview": "Live Theme Preview",
        "grp_theme_colors": "2. UI Color Palette Overrides",
        "btn_col_title": "🎨 Title Text Color",
        "btn_col_hint": "🎨 Hint Text Color",
        "btn_col_bat": "🎨 Battery Icon Color",
        "btn_reset_colors": "🔄 Reset to Theme Default Colors",
        "grp_sound_fx": "3. UI Sound Effects (Audio SFX)",
        "btn_sfx_nav": "🔊 Play Nav Click SFX",
        "btn_sfx_sel": "🔊 Play Open/Select SFX",
        "btn_sfx_back": "🔊 Play Back/Cancel SFX",
        "grp_shell": "4. Handheld Hardware Shell",
        "shell_grey": "Retro Classic Grey",
        "shell_white": "Arctic Pure White",
        "shell_black": "Transparent Black",
        "shell_purple": "Atomic Transparent Purple",

        # Tab 3: Tweaks
        "grp_hotkeys": "1. Hardware Hotkeys & Actions",
        "grp_cpu": "2. CPU Overclock & Performance",
        "grp_led": "3. Hardware RGB LEDs & Indicators",
        "grp_storage_tools": "4. Storage & File Management Tools",

        # Tab 4: Controls Guide
        "grp_keyboard_guide": "Keyboard Controls Mapping",
        "ctrl_dpad": "D-Pad (Up, Down, Left, Right)",
        "ctrl_dpad_keys": "W, S, A, D  or  Arrow Keys",
        "ctrl_btn_a": "A Button (Select / Open)",
        "ctrl_btn_a_keys": "J  or  Enter / Return",
        "ctrl_btn_b": "B Button (Back / Cancel)",
        "ctrl_btn_b_keys": "K  or  Escape / Backspace",
        "ctrl_btn_x": "X Button (Action / Close Slot)",
        "ctrl_btn_x_keys": "U  or  X",
        "ctrl_btn_y": "Y Button (Favorite / Secondary)",
        "ctrl_btn_y_keys": "I  or  Y",
        "ctrl_menu": "Menu Button (Game Switcher)",
        "ctrl_menu_keys": "M  or  Spacebar",
        "ctrl_shoulders": "L1 / R1 Shoulder Tabs",
        "ctrl_shoulders_keys": "Q  /  E",

        # Screen Canvas UI
        "ui_nav_open": "Open",
        "ui_nav_select": "Select",
        "ui_nav_back": "Back",
        "ui_nav_switcher": "Switcher",
        "ui_nav_tabs": "Tabs",
        "ui_nav_toggle": "Toggle",
        "ui_press_open": "PRESS [A] OPEN",
        
        "tab_name_favorites": "Favorites",
        "tab_sub_favorites": "Quick Access to Starred Games",
        "tab_name_games": "Games Hub",
        "tab_sub_games": "Browse All Consoles & ROMs",
        "tab_name_apps": "App Studio",
        "tab_sub_apps": "Productivity, Tools & Media",
        "tab_name_expert": "Retro Cores",
        "tab_sub_expert": "Standalone Cores & Emulators",
        "tab_name_settings": "Kayzit Settings",
        "tab_sub_settings": "System, Theme & Hardware",

        "view_title_consoles": "CONSOLES & SYSTEMS",
        "view_title_apps": "KAYZIT APPLICATIONS",
        "view_title_cores": "RETRO CORES & EXPERT",
        "view_title_settings": "SYSTEM PREFERENCES",
        "view_title_tweaks": "KAYZIT HARDWARE TWEAKS",
        "view_title_switcher": "KAYZIT INSTANT GAME SWITCHER",
        "view_title_activity": "ACTIVITY & PLAYTIME LOGS",

        "switcher_dock": "[A] RESUME GAME   •   [B] CLOSE   •   [X] CLOSE SLOT   •   [◀/▶] SWITCH",

        # Settings Items
        "setting_theme": "Theme Selection",
        "setting_theme_val": "Browse Themes",
        "setting_wifi": "Wi-Fi & Network",
        "setting_wifi_val": "Connected (RetroNet)",
        "setting_brightness": "Display & Brightness",
        "setting_brightness_val": "Level 8 / 10",
        "setting_volume": "Audio & Volume",
        "setting_volume_val": "Level 14 / 20",
        "setting_cpu": "Hardware Overclock",
        "setting_cpu_val": "1.4GHz Turbo Profile",
        "setting_rumble": "Haptic Rumble & Vibration",
        "setting_rumble_val": "Strength Level 7",
        "setting_clock": "Clock / NTP Time Sync",
        "setting_clock_val": "Auto (GMT+7)",
        "setting_storage": "Storage & MicroSD Card",
        "setting_storage_val": "MicroSD SDHC/XC",
        "setting_language": "Language / Ngôn ngữ",
        "setting_language_val": "English / Tiếng Việt",
        "setting_about": "About Kayzit OS",
        "setting_about_val": "v1.0.0 (SSD202D)",

        # Tweaks Items
        "tweak_quicksave": "Quick Save/Load on Exit",
        "tweak_quicksave_val": "Enabled",
        "tweak_quicksave_desc": "Auto save state when exiting and auto resume",
        "tweak_menu_tap": "Menu Button Single-Tap",
        "tweak_menu_tap_val": "Game Switcher",
        "tweak_menu_tap_desc": "Action when pressing Menu button once",
        "tweak_menu_hold": "Menu Button Long-Press",
        "tweak_menu_hold_val": "Exit to Menu",
        "tweak_menu_hold_desc": "Action when holding Menu button for 1s",
        "tweak_cpu": "CPU Overclock Profile",
        "tweak_cpu_val": "Smart Boost (1.4GHz)",
        "tweak_cpu_desc": "Dynamically boost CPU for heavy PS1/NDS games",
        "tweak_web": "Wi-Fi Web File Manager",
        "tweak_web_val": "Running (Port 80)",
        "tweak_web_desc": "Upload ROMs/Saves via web browser",
        "tweak_samba": "Samba File Sharing",
        "tweak_samba_val": "Active (\\\\miyoo)",
        "tweak_samba_desc": "Access SD card directly in Windows Explorer",
        "tweak_cloud": "Cloud Save Sync (Rclone)",
        "tweak_cloud_val": "Google Drive",
        "tweak_cloud_desc": "Auto sync game saves with cloud storage",
        "tweak_achieve": "RetroAchievements",
        "tweak_achieve_val": "Logged In",
        "tweak_achieve_desc": "Track retro game achievements online",
        "tweak_led": "Top LED Indicator",
        "tweak_led_val": "Battery Reactive",
        "tweak_led_desc": "LED behavior during gameplay and sleep",
    },

    "vi": {
        # App & Window
        "app_title": "Miyoo Mini Plus Studio & Bộ giả lập",
        "app_header": "🎮 Miyoo Mini Plus Studio & Trình mô phỏng",
        "lang_label": "🌐 Ngôn ngữ:",

        # Tabs
        "tab_boot": "💾 Thẻ nhớ & Khởi động",
        "tab_theme": "🎨 Giao diện & Theme",
        "tab_tweaks": "🕹️ Tinh chỉnh Miyoo",
        "tab_controls": "⌨️ Điều khiển & Hướng dẫn",

        # Tab 1: Source & Target
        "grp_source": "1. Thư mục Nguồn OS (Dùng để Xem trước Preview)",
        "btn_browse_src": "📁 Browse Nguồn...",
        "btn_refresh_src": "🔄",
        "hint_src": "💡 Máy Miyoo mô phỏng bên trái đang Xem trước (Preview) trực tiếp từ Thư mục Nguồn này.",
        "src_opt_kayzit": "⚡ Kayzit OS Payload (kayzit-os/payload)",
        "src_opt_workspace": "Thẻ ảo (Project Workspace)",
        "src_opt_custom": "Thư mục Payload tuỳ chỉnh",
        "src_prefix": "📁 Nguồn: ",

        "grp_target": "2. Ổ đĩa / Thư mục Đích (Thẻ nhớ MicroSD để Format & Sao chép)",
        "btn_browse_tgt": "📁 Browse Đích...",
        "btn_refresh_tgt": "🔄",
        "tgt_tag_sd": " [Thẻ MicroSD]",
        "tgt_tag_miyoo": " [Thẻ nhớ Miyoo]",
        "tgt_tag_drive": " [Ổ đĩa]",
        "tgt_virtual_export": "📁 Thư mục ảo Xuất Thẻ nhớ (virtual_sd_export)",
        "tgt_prefix": "📁 Đích: ",
        "tgt_info_free": "💾 Dung lượng trống: {free:.1f} GB / {total:.1f} GB ({path})",
        "tgt_info_missing": "📁 Thư mục chưa tồn tại (sẽ tự tạo khi sao chép): {path}",

        "grp_diag": "3. Chẩn đoán Bootloader Thư mục Nguồn (Preview)",
        "btn_reboot": "🔄 Kiểm tra lại & Khởi động lại giả lập",
        "boot_custom": "⚡ BOOT MODE: CUSTOM OS (THẺ NHỚ HOẠT ĐỘNG)",
        "boot_stock": "⚙️ BOOT MODE: STOCK OS (FIRMWARE GỐC NAND)",
        "boot_nosd": "⚠️ BOOT MODE: CHƯA CẮM THẺ NHỚ",
        "diag_source_path": "<b>Đường dẫn Thư mục Nguồn:</b> <code>{path}</code><br><br>",
        "diag_header": "<b>Chẩn đoán Khởi động:</b><br>",
        "diag_kernel": "• <b>Linux Kernel:</b> 🟢 Đã khởi tạo (Bộ nhớ NAND Flash)<br>",
        "diag_tmp_update": "• <b>.tmp_update/ :</b> {stat}<br>",
        "diag_payload": "• <b>OS Payload/ :</b> {stat}<br>",
        "diag_themes": "• <b>Themes/ :</b> {stat}<br>",
        "diag_roms": "• <b>Roms/ :</b> {stat}<br><br>",
        "diag_decision": "<b>Quyết định Khởi động:</b><br>{msg}",
        "stat_found_installed": "🟢 Đã tìm thấy (Đã cài đặt)",
        "stat_found_daemons": "🟢 Đã tìm thấy (MainUI & Daemons)",
        "stat_found_themes": "🟢 Đã tìm thấy ({count} themes)",
        "stat_found_roms": "🟢 Đã tìm thấy ({count} ROMs)",
        "stat_missing": "🔴 Chưa có",
        "stat_none": "⚪ Trống",

        "grp_deploy": "4. Công cụ Sao chép & Format Thẻ nhớ",
        "btn_deploy": "🚀 Sao chép & Format Thẻ nhớ (Nguồn ➔ Đích)",
        "btn_export_theme": "📂 Xuất Theme Nguồn sang Thẻ nhớ Đích (Themes/)",

        # Deployment Dialog
        "deploy_title": "🛠️ Format & Sao chép Hệ điều hành sang Thẻ nhớ",
        "deploy_header": "📦 Cài đặt & Sao chép Hệ điều hành sang Thẻ nhớ",
        "deploy_source_box": "📥 <b>Thư mục Nguồn (Previewing):</b><br><code style='color: #00f0ff; font-size: 12px;'>{path}</code>",
        "deploy_target_box": "📤 <b>Ổ đĩa / Thư mục Đích (Target SD):</b><br><code style='color: #34c759; font-size: 12px;'>{path}</code>",
        "deploy_grp_mode": "Chọn Chế độ Format / Cài đặt",
        "deploy_mode_preserve": "🛡️ Format tùy chỉnh (Giữ lại ROMs, Saves, BIOS cũ trên thẻ đích)",
        "deploy_mode_wipe": "⚠️ Format sạch 100% (Xóa sạch toàn bộ thẻ đích & chép nguồn sang)",
        "deploy_mode_update": "⚡ Cập nhật nhanh (Chỉ ghi đè hệ điều hành, không xóa bất kỳ file nào)",
        "deploy_grp_list": "Danh sách Dữ liệu trên Thẻ Đích sẽ được Bảo toàn:",
        "deploy_btn_sel_all": "✓ Chọn tất cả",
        "deploy_btn_desel": "✗ Bỏ chọn",
        "deploy_no_data": "⚪ Không tìm thấy ROMs/Saves cũ trên thẻ đích",
        "deploy_btn_cancel": "❌ Hủy bỏ",
        "deploy_btn_start": "🚀 Bắt đầu Sao chép & Cài đặt",
        "deploy_confirm_title": "Xác nhận Cài đặt & Sao chép",
        "deploy_confirm_msg": "Bạn có chắc chắn muốn sao chép từ Nguồn:\n{src}\n\nSang ổ đĩa Đích:\n{tgt}?\n\n• Chế độ: {mode}\n• Số mục bảo toàn: {count} mục",
        "deploy_mode_str_preserve": "Giữ lại ROMs/Saves đã chọn",
        "deploy_mode_str_wipe": "XÓA SẠCH TOÀN BỘ 100%",
        "deploy_mode_str_update": "Cập nhật nhanh hệ điều hành",
        "deploy_success_title": "Cài đặt Thành công!",
        "deploy_success_msg": "🎉 Hệ điều hành đã được sao chép hoàn tất vào:\n{path}!\n\nThẻ nhớ đã sẵn sàng để cắm vào máy Miyoo Mini Plus và sử dụng.",
        "deploy_error_title": "Lỗi Cài đặt",
        "deploy_error_msg": "Quá trình cài đặt gặp lỗi:\n{msg}",

        # Progress Strings
        "prog_backup": "📦 Đang sao lưu tạm ROMs, Saves & BIOS trên ổ đích...",
        "prog_clean_wipe": "🧹 Đang format sạch toàn bộ ổ đĩa thẻ nhớ đích...",
        "prog_clean_sys": "🧹 Đang dọn dẹp các tệp hệ điều hành cũ trên thẻ đích...",
        "prog_copying": "📥 Đang sao chép hệ điều hành từ Nguồn sang Đích...",
        "prog_copy_item": "📂 Đang sao chép: {item}...",
        "prog_hierarchy": "📁 Đang chuẩn hóa cấu trúc thư mục (Roms, Saves, BIOS, Themes)...",
        "prog_restore": "🔄 Đang khôi phục lại ROMs, Saves & BIOS đã bảo toàn...",
        "prog_done": "✅ Hoàn tất sao chép và chuẩn bị thẻ nhớ thành công!",

        # Tab 2: Theme Studio
        "grp_theme_select": "1. Bộ chọn Giao diện (Themes)",
        "lbl_theme_preview": "Ảnh Xem trước Theme",
        "grp_theme_colors": "2. Tùy biến Bảng màu Giao diện",
        "btn_col_title": "🎨 Màu Tiêu đề (Title)",
        "btn_col_hint": "🎨 Màu Hướng dẫn (Hints)",
        "btn_col_bat": "🎨 Màu Biểu tượng Pin",
        "btn_reset_colors": "🔄 Khôi phục Bảng màu Mặc định của Theme",
        "grp_sound_fx": "3. Hiệu ứng Âm thanh Giao diện (SFX)",
        "btn_sfx_nav": "🔊 Phát Tiếng Di chuyển (Nav Click)",
        "btn_sfx_sel": "🔊 Phát Tiếng Mở / Chọn (Open/Select)",
        "btn_sfx_back": "🔊 Phát Tiếng Quay lại (Back/Cancel)",
        "grp_shell": "4. Vỏ máy Cầm tay (Handheld Shell)",
        "shell_grey": "Xám Cổ điển (Classic Grey)",
        "shell_white": "Trắng Tinh khôi (Pure White)",
        "shell_black": "Đen Trong suốt (Transparent Black)",
        "shell_purple": "Tím Trong suốt (Atomic Purple)",

        # Tab 3: Tweaks
        "grp_hotkeys": "1. Phím tắt Nhanh & Thao tác Phần cứng",
        "grp_cpu": "2. Ép xung CPU & Hiệu năng",
        "grp_led": "3. Đèn LED RGB & Hiệu ứng Đèn đỉnh máy",
        "grp_storage_tools": "4. Công cụ Quản lý File & Bộ nhớ",

        # Tab 4: Controls Guide
        "grp_keyboard_guide": "Bảng Ánh xạ Phím Điều khiển Bàn phím",
        "ctrl_dpad": "D-Pad (Lên, Xuống, Trái, Phải)",
        "ctrl_dpad_keys": "W, S, A, D  hoặc  Các phím Mũi tên",
        "ctrl_btn_a": "Nút A (Chọn / Mở)",
        "ctrl_btn_a_keys": "J  hoặc  Phím Enter",
        "ctrl_btn_b": "Nút B (Quay lại / Hủy)",
        "ctrl_btn_b_keys": "K  hoặc  Phím Escape / Backspace",
        "ctrl_btn_x": "Nút X (Thao tác / Đóng Tab)",
        "ctrl_btn_x_keys": "U  hoặc  Phím X",
        "ctrl_btn_y": "Nút Y (Yêu thích / Tùy chọn)",
        "ctrl_btn_y_keys": "I  hoặc  Phím Y",
        "ctrl_menu": "Nút Menu (Chuyển game tức thì)",
        "ctrl_menu_keys": "M  hoặc  Phím Spacebar",
        "ctrl_shoulders": "Nút Vai L1 / R1 (Chuyển Tab)",
        "ctrl_shoulders_keys": "Q  /  E",

        # Screen Canvas UI
        "ui_nav_open": "Mở",
        "ui_nav_select": "Chọn",
        "ui_nav_back": "Trở về",
        "ui_nav_switcher": "Chuyển Game",
        "ui_nav_tabs": "Chuyển Tab",
        "ui_nav_toggle": "Bật/Tắt",
        "ui_press_open": "BẤM [A] ĐỂ MỞ",

        "tab_name_favorites": "Yêu thích",
        "tab_sub_favorites": "Truy cập nhanh các game đã ghim",
        "tab_name_games": "Kho Game Hub",
        "tab_sub_games": "Duyệt toàn bộ máy & ROMs",
        "tab_name_apps": "Ứng dụng Studio",
        "tab_sub_apps": "Công cụ, Tiện ích & Truyền thông",
        "tab_name_expert": "Lõi Retro Cores",
        "tab_sub_expert": "Bộ giả lập & Core độc lập",
        "tab_name_settings": "Cài đặt Kayzit",
        "tab_sub_settings": "Hệ thống, Giao diện & Phần cứng",

        "view_title_consoles": "HỆ MÁY GAME & PHẦN CỨNG",
        "view_title_apps": "ỨNG DỤNG HỆ ĐIỀU HÀNH",
        "view_title_cores": "LÕI GIẢ LẬP RETRO CORES",
        "view_title_settings": "CÀI ĐẶT HỆ THỐNG",
        "view_title_tweaks": "TINH CHỈNH PHẦN CỨNG",
        "view_title_switcher": "CHUYỂN GAME TỨC THÌ",
        "view_title_activity": "THỐNG KÊ THỜI GIAN CHƠI",

        "switcher_dock": "[A] TIẾP TỤC CHƠI   •   [B] ĐÓNG   •   [X] ĐÓNG SLOT   •   [◀/▶] CHỌN GAME",

        # Settings Items
        "setting_theme": "Lựa chọn Theme",
        "setting_theme_val": "Duyệt Themes",
        "setting_wifi": "Mạng Wi-Fi & Không dây",
        "setting_wifi_val": "Đã kết nối (RetroNet)",
        "setting_brightness": "Độ sáng Màn hình",
        "setting_brightness_val": "Mức 8 / 10",
        "setting_volume": "Âm lượng Loa",
        "setting_volume_val": "Mức 14 / 20",
        "setting_cpu": "Ép xung Phần cứng",
        "setting_cpu_val": "1.4GHz Turbo Boost",
        "setting_rumble": "Độ rung Phản hồi Haptic",
        "setting_rumble_val": "Cường độ Mức 7",
        "setting_clock": "Đồng hồ & Đồng bộ NTP",
        "setting_clock_val": "Tự động (GMT+7)",
        "setting_storage": "Thông tin Thẻ nhớ",
        "setting_storage_val": "MicroSD SDHC/XC",
        "setting_language": "Ngôn ngữ / Language",
        "setting_language_val": "English / Tiếng Việt",
        "setting_about": "Thông tin Kayzit OS",
        "setting_about_val": "v1.0.0 (SSD202D)",

        # Tweaks Items
        "tweak_quicksave": "Tự động Lưu/Tải khi Thoát",
        "tweak_quicksave_val": "Đã bật",
        "tweak_quicksave_desc": "Tự động lưu state khi thoát và mở lại đúng vị trí",
        "tweak_menu_tap": "Bấm 1 lần Nút Menu",
        "tweak_menu_tap_val": "Chuyển Game Nhanh",
        "tweak_menu_tap_desc": "Hành động khi nhấn nút Menu một lần",
        "tweak_menu_hold": "Giữ Nút Menu 1 giây",
        "tweak_menu_hold_val": "Thoát ra Menu chính",
        "tweak_menu_hold_desc": "Hành động khi giữ phím Menu trong 1 giây",
        "tweak_cpu": "Cấu hình Ép xung CPU",
        "tweak_cpu_val": "Smart Boost (1.4GHz)",
        "tweak_cpu_desc": "Tự động tăng xung nhịp cho các game PS1/NDS nặng",
        "tweak_web": "Quản lý File qua Trình duyệt Web",
        "tweak_web_val": "Đang chạy (Cổng 80)",
        "tweak_web_desc": "Tải ROMs/Saves trực tiếp qua mạng không dây",
        "tweak_samba": "Chia sẻ Ổ đĩa Samba",
        "tweak_samba_val": "Đang bật (\\\\miyoo)",
        "tweak_samba_desc": "Truy cập thẻ nhớ trực tiếp từ Windows Explorer",
        "tweak_cloud": "Đồng bộ Đám mây (Rclone)",
        "tweak_cloud_val": "Google Drive",
        "tweak_cloud_desc": "Tự động sao lưu save game lên Google Drive",
        "tweak_achieve": "Thành tích RetroAchievements",
        "tweak_achieve_val": "Đã đăng nhập",
        "tweak_achieve_desc": "Theo dõi danh hiệu và thành tích game cổ điển",
        "tweak_led": "Đèn LED Đỉnh máy",
        "tweak_led_val": "Phản hồi theo Mức Pin",
        "tweak_led_desc": "Hiệu ứng đèn LED khi chơi game và chế độ ngủ",
    }
}

def tr(key, **kwargs):
    """Translate key to current language with optional formatting."""
    lang_dict = TRANSLATIONS.get(CURRENT_LANG, TRANSLATIONS["en"])
    text = lang_dict.get(key, TRANSLATIONS["en"].get(key, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text

def get_language():
    return CURRENT_LANG

def set_language(lang_code):
    global CURRENT_LANG
    if lang_code in TRANSLATIONS:
        CURRENT_LANG = lang_code
        notify_listeners()

def add_listener(callback):
    if callback not in _LISTENERS:
        _LISTENERS.append(callback)

def remove_listener(callback):
    if callback in _LISTENERS:
        _LISTENERS.remove(callback)

def notify_listeners():
    for cb in list(_LISTENERS):
        try:
            cb()
        except Exception:
            pass
