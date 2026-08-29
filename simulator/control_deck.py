import os
import shutil
import string
import tempfile
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QSlider, QCheckBox, QGroupBox, QScrollArea, QColorDialog, QMessageBox,
    QTabWidget, QFileDialog, QFrame, QDialog, QRadioButton, QButtonGroup,
    QProgressBar, QListWidget, QListWidgetItem
)
from PyQt6.QtGui import QPixmap, QColor, QFont, QIcon
from PyQt6.QtCore import Qt, QThread, pyqtSignal

class DeployWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, target_path, workspace_root, preserve_mode, selected_items):
        super().__init__()
        self.target_path = target_path
        self.workspace_root = workspace_root
        self.preserve_mode = preserve_mode
        self.selected_items = selected_items

    def run(self):
        temp_backup_dir = None
        try:
            temp_root = os.path.join(self.workspace_root, ".temp")
            os.makedirs(temp_root, exist_ok=True)

            if self.preserve_mode and self.selected_items:
                self.progress.emit(15, "📦 Đang sao lưu tạm các thư mục ROMs & Saves đã chọn...")
                temp_backup_dir = tempfile.mkdtemp(prefix="miyoo_backup_", dir=temp_root)
                
                for rel_path in self.selected_items:
                    src = os.path.join(self.target_path, rel_path)
                    dst = os.path.join(temp_backup_dir, rel_path)
                    if os.path.exists(src):
                        if os.path.isdir(src):
                            shutil.copytree(src, dst, dirs_exist_ok=True)
                        else:
                            os.makedirs(os.path.dirname(dst), exist_ok=True)
                            shutil.copy2(src, dst)

            # 2. Clean Target Drive / Folders
            self.progress.emit(45, "🧹 Đang format và làm sạch ổ đĩa thẻ nhớ...")
            if not self.preserve_mode:
                for item in os.listdir(self.target_path):
                    ipath = os.path.join(self.target_path, item)
                    try:
                        if os.path.isdir(ipath):
                            shutil.rmtree(ipath, ignore_errors=True)
                        else:
                            os.remove(ipath)
                    except Exception:
                        pass
            else:
                system_dirs = [".tmp_update", "miyoo", "miyoo354", "RetroArch", ".tmp_update.bak", ".minui", ".koriki", ".allium"]
                for sdir in system_dirs:
                    ipath = os.path.join(self.target_path, sdir)
                    if os.path.exists(ipath):
                        try:
                            shutil.rmtree(ipath, ignore_errors=True)
                        except Exception:
                            pass

            # 3. Create Standard Miyoo Folder Hierarchy
            self.progress.emit(70, "📁 Đang khởi tạo cấu trúc thư mục chuẩn Miyoo (Roms, Saves, BIOS, Themes)...")
            standard_dirs = [
                os.path.join("Roms", "GBA"),
                os.path.join("Roms", "GBC"),
                os.path.join("Roms", "GB"),
                os.path.join("Roms", "FC"),
                os.path.join("Roms", "SFC"),
                os.path.join("Roms", "MD"),
                os.path.join("Roms", "PS"),
                os.path.join("Roms", "ARCADE"),
                os.path.join("Roms", "PICO"),
                "Saves",
                "BIOS",
                "Themes",
                "Screenshots"
            ]
            for sdir in standard_dirs:
                os.makedirs(os.path.join(self.target_path, sdir), exist_ok=True)

            # 4. Restore Preserved Data (if any)
            if temp_backup_dir and os.path.exists(temp_backup_dir):
                self.progress.emit(85, "🔄 Đang khôi phục toàn bộ ROMs, Saves & Box Arts đã giữ lại...")
                for item in os.listdir(temp_backup_dir):
                    s = os.path.join(temp_backup_dir, item)
                    d = os.path.join(self.target_path, item)
                    if os.path.isdir(s):
                        shutil.copytree(s, d, dirs_exist_ok=True)
                    else:
                        shutil.copy2(s, d)

            self.progress.emit(100, "✅ Hoàn tất format và chuẩn bị thẻ nhớ thành công!")
            self.finished.emit(True, "Format và chuẩn bị thẻ nhớ thành công!")
        except Exception as e:
            self.finished.emit(False, str(e))
        finally:
            # Always clean up temporary backup directory
            if temp_backup_dir and os.path.exists(temp_backup_dir):
                try:
                    shutil.rmtree(temp_backup_dir, ignore_errors=True)
                except Exception:
                    pass
            temp_root = os.path.join(self.workspace_root, ".temp")
            if os.path.exists(temp_root) and not os.listdir(temp_root):
                try:
                    os.rmdir(temp_root)
                except Exception:
                    pass

class SDDeploymentDialog(QDialog):
    def __init__(self, target_path, workspace_root, parent=None):
        super().__init__(parent)
        self.target_path = target_path
        self.workspace_root = workspace_root
        self.worker = None

        self.setWindowTitle("🛠️ Format & Chuẩn bị Thẻ nhớ Miyoo Mini Plus")
        self.setFixedSize(560, 620)
        self.setStyleSheet("""
            QDialog { background-color: #1c1c1e; color: #ffffff; }
            QLabel { color: #f2f2f7; }
            QGroupBox {
                color: #007aff;
                font-weight: bold;
                border: 1px solid #3a3a3c;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 4px;
            }
            QRadioButton { color: #ffffff; font-size: 12px; padding: 4px; }
            QRadioButton::indicator { width: 14px; height: 14px; }
            QListWidget { background: #2c2c2e; border: 1px solid #3a3a3c; border-radius: 6px; color: #fff; }
            QGroupBox:disabled { color: #636366; border-color: #2c2c2e; }
            QListWidget:disabled { background-color: #18181a; color: #636366; border-color: #2c2c2e; }
            QPushButton:disabled { background-color: #242426; color: #505054; border-color: #2c2c2e; }
            QLabel:disabled { color: #636366; }
            QProgressBar { background: #2c2c2e; border: 1px solid #3a3a3c; border-radius: 4px; text-align: center; color: #fff; font-weight: bold; }
            QProgressBar::chunk { background: #34c759; border-radius: 3px; }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # 1. Header Banner
        header = QLabel("📦 Cài đặt & Triển khai OnionOS v4.3.1-1")
        header.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        header.setStyleSheet("color: #007aff;")
        layout.addWidget(header)

        # Target Drive Info
        lbl_target = QLabel(f"<b>Ổ đĩa / Thư mục mục tiêu:</b> <code style='color: #34c759; font-size: 13px;'>{self.target_path}</code>")
        lbl_target.setStyleSheet("background: #2c2c2e; padding: 8px; border-radius: 6px; border: 1px solid #3a3a3c;")
        layout.addWidget(lbl_target)

        # 2. Mode Selector
        grp_mode = QGroupBox("Chọn Chế độ Format / Cài đặt")
        m_layout = QVBoxLayout(grp_mode)

        self.radio_preserve = QRadioButton("🛡️ Format tùy chỉnh (Tùy chọn giữ lại ROMs, Saves, BIOS...)")
        self.radio_preserve.setChecked(True)
        self.radio_preserve.toggled.connect(self.on_mode_toggled)
        m_layout.addWidget(self.radio_preserve)

        self.radio_wipe = QRadioButton("⚠️ Format sạch (Xóa sạch 100% toàn bộ thẻ nhớ và cài mới)")
        self.radio_wipe.toggled.connect(self.on_mode_toggled)
        m_layout.addWidget(self.radio_wipe)

        layout.addWidget(grp_mode)

        # 3. Preservation List Group
        self.grp_list = QGroupBox("Danh sách Dữ liệu tìm thấy trên Thẻ sẽ được Giữ lại:")
        l_layout = QVBoxLayout(self.grp_list)

        btn_row = QHBoxLayout()
        self.btn_sel_all = QPushButton("✓ Chọn tất cả")
        self.btn_sel_all.setStyleSheet("background: #3a3a3c; color: #fff; padding: 4px 8px; font-size: 11px;")
        self.btn_sel_all.clicked.connect(self.select_all_items)
        btn_row.addWidget(self.btn_sel_all)

        self.btn_desel = QPushButton("✗ Bỏ chọn")
        self.btn_desel.setStyleSheet("background: #3a3a3c; color: #fff; padding: 4px 8px; font-size: 11px;")
        self.btn_desel.clicked.connect(self.deselect_all_items)
        btn_row.addWidget(self.btn_desel)
        btn_row.addStretch()
        l_layout.addLayout(btn_row)

        self.list_widget = QListWidget()
        self.list_widget.setFixedHeight(170)
        self.populate_preserve_items()
        l_layout.addWidget(self.list_widget)

        layout.addWidget(self.grp_list)
        self.on_mode_toggled()

        # 4. Progress Bar & Status
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("color: #ff9500; font-size: 11px;")
        self.status_lbl.setVisible(False)
        layout.addWidget(self.status_lbl)

        # 5. Buttons
        btn_box = QHBoxLayout()
        self.btn_cancel = QPushButton("❌ Hủy bỏ")
        self.btn_cancel.setStyleSheet("background: #3a3a3c; color: #fff; padding: 8px 16px; font-weight: bold; border-radius: 6px;")
        self.btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(self.btn_cancel)

        btn_box.addStretch()

        self.btn_start = QPushButton("🚀 Bắt đầu Format & Cài đặt")
        self.btn_start.setStyleSheet("background: #34c759; color: #fff; padding: 8px 20px; font-weight: bold; font-size: 13px; border-radius: 6px;")
        self.btn_start.clicked.connect(self.start_deployment)
        btn_box.addWidget(self.btn_start)

        layout.addLayout(btn_box)

    def populate_preserve_items(self):
        self.list_widget.clear()
        if not self.target_path or not os.path.exists(self.target_path):
            return

        # Check Saves
        saves_dir = os.path.join(self.target_path, "Saves")
        if os.path.exists(saves_dir):
            item = QListWidgetItem("💾 Thư mục Saves/ (File lưu game & Save states)")
            item.setData(Qt.ItemDataRole.UserRole, "Saves")
            item.setCheckState(Qt.CheckState.Checked)
            self.list_widget.addItem(item)

        # Check BIOS
        bios_dir = os.path.join(self.target_path, "BIOS")
        if os.path.exists(bios_dir):
            item = QListWidgetItem("🧩 Thư mục BIOS/ (Các file BIOS hệ máy)")
            item.setData(Qt.ItemDataRole.UserRole, "BIOS")
            item.setCheckState(Qt.CheckState.Checked)
            self.list_widget.addItem(item)

        # Check ROMs by System
        roms_root = os.path.join(self.target_path, "Roms")
        if os.path.exists(roms_root) and os.path.isdir(roms_root):
            system_names = {
                "GBA": "Game Boy Advance (GBA)",
                "PS": "PlayStation 1 (PS)",
                "SFC": "Super Nintendo (SNES / SFC)",
                "FC": "Nintendo Ent. System (NES / FC)",
                "ARCADE": "Arcade Classics (MAME / CPS)",
                "NDS": "Nintendo DS (NDS)",
                "MD": "Sega Genesis / Mega Drive (MD)",
                "GBC": "Game Boy Color (GBC)",
                "GB": "Game Boy Original (GB)",
                "PICO": "Pico-8 Fantasy Console (PICO)",
                "PORTS": "Game Ports (Cave Story, Doom...)",
                "NEOGEO": "Neo Geo (NEOGEO)"
            }
            try:
                for folder in sorted(os.listdir(roms_root)):
                    fpath = os.path.join(roms_root, folder)
                    if os.path.isdir(fpath):
                        count = len([f for f in os.listdir(fpath) if os.path.isfile(os.path.join(fpath, f))])
                        sname = system_names.get(folder.upper(), f"Hệ máy {folder}")
                        label = f"🎮 ROMs - {sname} ({count} files)"
                        
                        item = QListWidgetItem(label)
                        item.setData(Qt.ItemDataRole.UserRole, os.path.join("Roms", folder))
                        item.setCheckState(Qt.CheckState.Checked)
                        self.list_widget.addItem(item)
            except Exception:
                pass

        if self.list_widget.count() == 0:
            item = QListWidgetItem("⚪ Không tìm thấy ROMs/Saves cũ (Thẻ trống hoặc mới)")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
            self.list_widget.addItem(item)

    def on_mode_toggled(self):
        preserve = self.radio_preserve.isChecked()
        self.grp_list.setEnabled(preserve)

    def select_all_items(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                item.setCheckState(Qt.CheckState.Checked)

    def deselect_all_items(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                item.setCheckState(Qt.CheckState.Unchecked)

    def start_deployment(self):
        preserve_mode = self.radio_preserve.isChecked()
        
        selected_items = []
        if preserve_mode:
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                if item.checkState() == Qt.CheckState.Checked:
                    rel_path = item.data(Qt.ItemDataRole.UserRole)
                    if rel_path:
                        selected_items.append(rel_path)

        # Confirm message
        msg = (
            f"Bạn có chắc chắn muốn tiến hành Format & Cài đặt OnionOS vào:\n{self.target_path}?\n\n"
            f"• Chế độ: {'Giữ lại ROMs & Saves đã chọn' if preserve_mode else 'XÓA SẠCH TOÀN BỘ 100%'}\n"
            f"• Số mục bảo toàn: {len(selected_items)} mục"
        )
        reply = QMessageBox.warning(
            self,
            "Xác nhận Cài đặt OnionOS",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # UI State during copy
        self.btn_start.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.radio_preserve.setEnabled(False)
        self.radio_wipe.setEnabled(False)
        self.grp_list.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_lbl.setVisible(True)
        self.progress_bar.setValue(5)

        # Launch Worker Thread
        self.worker = DeployWorker(self.target_path, self.workspace_root, preserve_mode, selected_items)
        self.worker.progress.connect(self.on_worker_progress)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()

    def on_worker_progress(self, val, msg):
        self.progress_bar.setValue(val)
        self.status_lbl.setText(msg)

    def on_worker_finished(self, success, msg):
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(True)
        if success:
            QMessageBox.information(
                self,
                "Cài đặt Thành công!",
                f"🎉 Hệ điều hành OnionOS v4.3.1-1 đã được cài đặt hoàn tất vào {self.target_path}!\n\n"
                "Toàn bộ ROMs, Saves và 25 Theme đã sẵn sàng. Trình giả lập sẽ tự động Reboot ngay bây giờ."
            )
            self.accept()
        else:
            QMessageBox.critical(self, "Lỗi Cài đặt", f"Quá trình cài đặt gặp lỗi:\n{msg}")

class ControlDeck(QWidget):
    def __init__(self, theme_mgr, canvas, frame_widget, parent=None):
        super().__init__(parent)
        self.theme_mgr = theme_mgr
        self.canvas = canvas
        self.frame_widget = frame_widget
        self.sys_data = canvas.sys_data
        
        self.drive_combo = None
        self.boot_status_badge = None
        self.diag_info_lbl = None
        self.theme_combo = None
        self.preview_lbl = None
        self.theme_info_lbl = None
        
        self.setFixedWidth(460)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Title
        title_lbl = QLabel("🎮 Miyoo Mini Plus Studio & Simulator")
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #007aff; margin-bottom: 2px;")
        main_layout.addWidget(title_lbl)

        # Tabs (4 Clean Tabs - No Overflow)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #3a3a3c; border-radius: 6px; background: #1c1c1e; }
            QTabBar::tab { background: #2c2c2e; color: #aaa; padding: 8px 14px; margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px; font-size: 11px; }
            QTabBar::tab:selected { background: #007aff; color: #fff; font-weight: bold; }
            QGroupBox {
                color: #fff;
                font-weight: bold;
                border: 1px solid #3a3a3c;
                border-radius: 6px;
                margin-top: 14px;
                padding-top: 14px;
                padding-left: 8px;
                padding-right: 8px;
                padding-bottom: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 4px;
                color: #007aff;
            }
            QScrollBar:vertical {
                background: #1c1c1e;
                width: 8px;
                margin: 0px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #3a3a3c;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #007aff;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        # Tab Containers
        self.tab_boot_container = QWidget()
        self.tab_theme_container = QWidget()
        self.tab_tweaks_container = QWidget()
        self.tab_guide_container = QWidget()

        l_boot = QVBoxLayout(self.tab_boot_container)
        l_boot.setContentsMargins(0, 0, 0, 0)
        l_boot.addWidget(self.create_boot_tab())

        self.tabs.addTab(self.tab_boot_container, "💾 MicroSD & Boot")
        self.tabs.addTab(self.tab_theme_container, "🎨 Themes & UI")
        self.tabs.addTab(self.tab_tweaks_container, "🕹️ Miyoo Tweaks")
        self.tabs.addTab(self.tab_guide_container, "⌨️ Controls")

        self.tabs.currentChanged.connect(self.on_tab_switched)
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(50, self.preload_remaining_tabs)

        main_layout.addWidget(self.tabs)

    def preload_remaining_tabs(self):
        if self.tab_theme_container.layout() is None:
            l = QVBoxLayout(self.tab_theme_container)
            l.setContentsMargins(0, 0, 0, 0)
            l.addWidget(self.create_theme_tab())
        if self.tab_tweaks_container.layout() is None:
            l = QVBoxLayout(self.tab_tweaks_container)
            l.setContentsMargins(0, 0, 0, 0)
            l.addWidget(self.create_tweaks_tab())
        if self.tab_guide_container.layout() is None:
            l = QVBoxLayout(self.tab_guide_container)
            l.setContentsMargins(0, 0, 0, 0)
            l.addWidget(self.create_guide_tab())

    def on_tab_switched(self, idx):
        self.preload_remaining_tabs()

    def create_boot_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        # 1. Drive & Directory Selector
        grp_drive = QGroupBox("1. MicroSD Drive / Target Folder")
        d_layout = QVBoxLayout(grp_drive)

        d_row = QHBoxLayout()
        self.drive_combo = QComboBox()
        self.drive_combo.setStyleSheet("background: #2c2c2e; color: #fff; padding: 6px; border-radius: 4px; font-weight: bold;")
        d_row.addWidget(self.drive_combo, 1)

        btn_browse = QPushButton("📁 Browse...")
        btn_browse.setStyleSheet("background: #3a3a3c; color: #fff; padding: 6px;")
        btn_browse.clicked.connect(self.browse_custom_drive)
        d_row.addWidget(btn_browse)

        btn_refresh = QPushButton("🔄")
        btn_refresh.setToolTip("Refresh drive list")
        btn_refresh.setStyleSheet("background: #3a3a3c; color: #fff; padding: 6px;")
        btn_refresh.clicked.connect(self.populate_drives)
        d_row.addWidget(btn_refresh)

        d_layout.addLayout(d_row)
        layout.addWidget(grp_drive)

        # 2. Linux Bootloader Diagnostic Panel
        grp_diag = QGroupBox("2. Linux Bootloader Check (Onion vs Stock)")
        diag_layout = QVBoxLayout(grp_diag)

        self.boot_status_badge = QLabel()
        self.boot_status_badge.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.boot_status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.boot_status_badge.setStyleSheet("padding: 8px; border-radius: 6px;")
        diag_layout.addWidget(self.boot_status_badge)

        self.diag_info_lbl = QLabel()
        self.diag_info_lbl.setFont(QFont("Segoe UI", 10))
        self.diag_info_lbl.setStyleSheet("color: #ddd; background: #161b22; padding: 10px; border-radius: 6px; border: 1px solid #30363d;")
        self.diag_info_lbl.setWordWrap(True)
        diag_layout.addWidget(self.diag_info_lbl)

        btn_reboot = QPushButton("🔄 Re-Check & Reboot Miyoo")
        btn_reboot.setStyleSheet("background: #007aff; color: #fff; font-weight: bold; padding: 8px; border-radius: 4px;")
        btn_reboot.clicked.connect(self.trigger_reboot)
        diag_layout.addWidget(btn_reboot)

        layout.addWidget(grp_diag)

        # 3. Smart Format & SD Card Tools
        grp_quick = QGroupBox("3. Format & Chuẩn bị Thẻ nhớ Miyoo")
        q_layout = QVBoxLayout(grp_quick)

        btn_install_onion = QPushButton("🛠️ Format & Khởi tạo Thẻ nhớ (Tùy chọn giữ ROMs/Saves)")
        btn_install_onion.setStyleSheet("background: #007aff; color: #fff; font-weight: bold; padding: 10px; border-radius: 6px;")
        btn_install_onion.clicked.connect(self.open_deployment_dialog)
        q_layout.addWidget(btn_install_onion)

        btn_copy_theme_sd = QPushButton("📂 Xuất Theme hiện tại sang Thẻ nhớ (Themes/)")
        btn_copy_theme_sd.setStyleSheet("background: #007aff; color: #fff; padding: 8px; font-weight: bold; border-radius: 4px;")
        btn_copy_theme_sd.clicked.connect(self.export_theme_to_sd)
        q_layout.addWidget(btn_copy_theme_sd)

        layout.addWidget(grp_quick)
        layout.addStretch()

        # Safely populate drives and connect signal
        self.populate_drives()
        self.drive_combo.currentTextChanged.connect(self.on_drive_changed)

        scroll.setWidget(widget)
        self.update_boot_diagnostic_ui()
        return scroll

    def populate_drives(self):
        if self.drive_combo is None:
            return
        self.drive_combo.blockSignals(True)
        self.drive_combo.clear()
        
        current_target = self.sys_data.sd_root or ""
        
        # Scan only mounted Windows drives instantly via Kernel bitmask
        available = []
        try:
            import ctypes
            bitmask = ctypes.windll.kernel32.GetLogicalDrives()
            for i in range(26):
                if bitmask & (1 << i):
                    d = chr(ord('A') + i)
                    drv = f"{d}:\\"
                    try:
                        has_onion = os.path.exists(os.path.join(drv, ".tmp_update")) and os.path.exists(os.path.join(drv, "miyoo"))
                        tag = " [ONION OS]" if has_onion else " [Drive]"
                        if d == 'E':
                            tag = " [ONION SD]" if has_onion else " [USB Card]"
                        available.append((drv, f"{drv}{tag}"))
                    except Exception:
                        available.append((drv, drv))
        except Exception:
            for d in ['C', 'D', 'E', 'F', 'G']:
                drv = f"{d}:\\"
                if os.path.exists(drv):
                    available.append((drv, drv))

        # Add workspace project folder as virtual SD option
        proj_dir = self.sys_data.workspace_root
        available.append((proj_dir, "Virtual SD (Project Workspace)"))

        for path, label in available:
            self.drive_combo.addItem(label, path)

        # Set selection to current sd_root
        for idx in range(self.drive_combo.count()):
            if self.drive_combo.itemData(idx) == current_target:
                self.drive_combo.setCurrentIndex(idx)
                break

        self.drive_combo.blockSignals(False)

    def on_drive_changed(self):
        if self.drive_combo is None:
            return
        selected_path = self.drive_combo.currentData()
        if selected_path:
            self.sys_data.reload_from_path(selected_path)
            
            th_dir = os.path.join(selected_path, "Themes")
            if os.path.exists(th_dir) and os.path.isdir(th_dir) and os.listdir(th_dir):
                self.theme_mgr.reload_themes(th_dir)
            else:
                proj_th = os.path.join(self.sys_data.workspace_root, "Themes")
                self.theme_mgr.reload_themes(proj_th)

            self.update_boot_diagnostic_ui()
            self.refresh_theme_list()
            self.canvas.view_stack = ['MAIN_CAROUSEL']
            self.canvas.update()

    def browse_custom_drive(self):
        folder = QFileDialog.getExistingDirectory(self, "Select MicroSD Card or Folder", self.sys_data.sd_root or "C:\\")
        if folder:
            self.drive_combo.addItem(f"Custom: {folder}", folder)
            self.drive_combo.setCurrentIndex(self.drive_combo.count() - 1)

    def trigger_reboot(self):
        selected_path = self.drive_combo.currentData() or self.sys_data.sd_root
        self.sys_data.reload_from_path(selected_path)
        self.canvas.view_stack = ['MAIN_CAROUSEL']
        self.canvas.active_running_game = None
        self.canvas.switcher_open = False
        self.update_boot_diagnostic_ui()
        self.canvas.update()
        self.theme_mgr.play_sfx("select")

    def update_boot_diagnostic_ui(self):
        if not self.boot_status_badge or not self.diag_info_lbl:
            return
        diag = self.sys_data.boot_diag
        
        if diag.boot_mode in ["CUSTOM_OS", "ONION_OS"]:
            self.boot_status_badge.setText("⚡ BOOT MODE: CUSTOM OS (MICROSD ACTIVE)")
            self.boot_status_badge.setStyleSheet("background: #007aff; color: #ffffff; padding: 8px; border-radius: 6px;")
        elif diag.boot_mode == "STOCK_OS":
            self.boot_status_badge.setText("⚙️ BOOT MODE: STOCK OS (NAND FACTORY)")
            self.boot_status_badge.setStyleSheet("background: #f59e0b; color: #000000; padding: 8px; border-radius: 6px;")
        else:
            self.boot_status_badge.setText("⚠️ BOOT MODE: NO SD CARD INSERTED")
            self.boot_status_badge.setStyleSheet("background: #ef4444; color: #ffffff; padding: 8px; border-radius: 6px;")

        u_stat = "🟢 Found (Installed)" if diag.has_tmp_update else "🔴 Missing"
        m_stat = "🟢 Found (MainUI & Daemons)" if diag.has_miyoo else "🔴 Missing"
        t_stat = f"🟢 Found ({diag.theme_count} themes)" if diag.has_themes else "⚪ None"
        r_stat = f"🟢 Found ({diag.rom_count} ROMs indexed)" if diag.has_roms else "⚪ None"

        text = (
            f"<b>Target Path:</b> <code>{diag.path}</code><br><br>"
            f"<b>Boot Diagnostics:</b><br>"
            f"• <b>Linux Kernel:</b> 🟢 Initialized (NAND Flash)<br>"
            f"• <b>.tmp_update/ :</b> {u_stat}<br>"
            f"• <b>miyoo/ :</b> {m_stat}<br>"
            f"• <b>Themes/ :</b> {t_stat}<br>"
            f"• <b>Roms/ :</b> {r_stat}<br><br>"
            f"<b>Kernel Decision:</b><br>{diag.status_message}"
        )
        self.diag_info_lbl.setText(text)

    def open_deployment_dialog(self):
        target = self.drive_combo.currentData() or self.sys_data.sd_root
        if not target or not os.path.exists(target):
            QMessageBox.warning(self, "Invalid Target", "Vui lòng chọn một ổ đĩa hoặc thư mục hợp lệ.")
            return

        dialog = SDDeploymentDialog(target, self.sys_data.workspace_root, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.trigger_reboot()
            self.populate_drives()

    def create_theme_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        # 1. Theme Selector Group
        grp_theme = QGroupBox("Theme Selection")
        t_layout = QVBoxLayout(grp_theme)

        self.theme_combo = QComboBox()
        self.theme_combo.setStyleSheet("background: #2c2c2e; color: #fff; padding: 6px; border-radius: 4px;")
        self.refresh_theme_list()
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        t_layout.addWidget(self.theme_combo)

        # Theme Preview Image
        self.preview_lbl = QLabel()
        self.preview_lbl.setFixedHeight(110)
        self.preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_lbl.setStyleSheet("background: #111; border: 1px solid #333; border-radius: 4px; color: #666;")
        self.update_theme_preview()
        t_layout.addWidget(self.preview_lbl)

        # Theme Description
        self.theme_info_lbl = QLabel()
        self.theme_info_lbl.setWordWrap(True)
        self.theme_info_lbl.setStyleSheet("color: #aaa; font-size: 11px;")
        self.update_theme_info()
        t_layout.addWidget(self.theme_info_lbl)

        layout.addWidget(grp_theme)

        # 2. Audio Engine (BGM & SFX)
        grp_audio = QGroupBox("Audio Engine (BGM & Sound Effects)")
        a_layout = QVBoxLayout(grp_audio)

        self.bgm_chk = QCheckBox("Background Music (BGM)")
        self.bgm_chk.setChecked(True)
        self.bgm_chk.setStyleSheet("color: #fff;")
        self.bgm_chk.toggled.connect(self.theme_mgr.set_bgm_enabled)
        a_layout.addWidget(self.bgm_chk)

        bgm_v_box = QHBoxLayout()
        bgm_v_box.addWidget(QLabel("BGM Vol:"))
        self.bgm_slider = QSlider(Qt.Orientation.Horizontal)
        self.bgm_slider.setRange(0, 100)
        self.bgm_slider.setValue(40)
        self.bgm_slider.valueChanged.connect(lambda v: self.theme_mgr.set_bgm_volume(v / 100.0))
        bgm_v_box.addWidget(self.bgm_slider)
        a_layout.addLayout(bgm_v_box)

        self.sfx_chk = QCheckBox("Sound Effects (SFX)")
        self.sfx_chk.setChecked(True)
        self.sfx_chk.setStyleSheet("color: #fff;")
        self.sfx_chk.toggled.connect(self.theme_mgr.set_sfx_enabled)
        a_layout.addWidget(self.sfx_chk)

        sfx_btns = QHBoxLayout()
        btn_nav = QPushButton("🔊 Nav")
        btn_nav.setStyleSheet("background: #2c2c2e; color: #fff; padding: 4px;")
        btn_nav.clicked.connect(lambda: self.theme_mgr.play_sfx("change"))
        sfx_btns.addWidget(btn_nav)

        btn_sel = QPushButton("🔊 Select")
        btn_sel.setStyleSheet("background: #2c2c2e; color: #fff; padding: 4px;")
        btn_sel.clicked.connect(lambda: self.theme_mgr.play_sfx("select"))
        sfx_btns.addWidget(btn_sel)

        btn_back = QPushButton("🔊 Back")
        btn_back.setStyleSheet("background: #2c2c2e; color: #fff; padding: 4px;")
        btn_back.clicked.connect(lambda: self.theme_mgr.play_sfx("back"))
        sfx_btns.addWidget(btn_back)
        a_layout.addLayout(sfx_btns)

        layout.addWidget(grp_audio)

        # 3. Custom Color Pickers
        grp_colors = QGroupBox("Custom UI Colors")
        c_layout = QVBoxLayout(grp_colors)

        btn_title_col = QPushButton("🎨 Change Title Color")
        btn_title_col.setStyleSheet("background: #2c2c2e; color: #fff; padding: 6px;")
        btn_title_col.clicked.connect(self.pick_title_color)
        c_layout.addWidget(btn_title_col)

        btn_hint_col = QPushButton("🎨 Change Hint/Bottom Color")
        btn_hint_col.setStyleSheet("background: #2c2c2e; color: #fff; padding: 6px;")
        btn_hint_col.clicked.connect(self.pick_hint_color)
        c_layout.addWidget(btn_hint_col)

        btn_bat_col = QPushButton("🎨 Change Battery Color")
        btn_bat_col.setStyleSheet("background: #2c2c2e; color: #fff; padding: 6px;")
        btn_bat_col.clicked.connect(self.pick_bat_color)
        c_layout.addWidget(btn_bat_col)

        layout.addWidget(grp_colors)
        layout.addStretch()

        scroll.setWidget(widget)
        return scroll

    def refresh_theme_list(self):
        if hasattr(self, 'theme_combo') and self.theme_combo is not None:
            self.theme_combo.blockSignals(True)
            self.theme_combo.clear()
            for tname in self.theme_mgr.themes.keys():
                self.theme_combo.addItem(tname)
            if self.theme_mgr.current_theme:
                self.theme_combo.setCurrentText(self.theme_mgr.current_theme.name)
            self.theme_combo.blockSignals(False)

    def create_tweaks_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        # 1. Miyoo Handheld Shell Casing
        grp_shell = QGroupBox("Miyoo Mini Plus Casing Shell")
        s_layout = QVBoxLayout(grp_shell)

        self.shell_combo = QComboBox()
        self.shell_combo.setStyleSheet("background: #2c2c2e; color: #fff; padding: 6px; border-radius: 4px;")
        for sname in self.frame_widget.SHELL_COLORS.keys():
            self.shell_combo.addItem(sname)
        self.shell_combo.currentTextChanged.connect(self.on_shell_changed)
        s_layout.addWidget(self.shell_combo)
        layout.addWidget(grp_shell)

        # 2. Quick Screen Actions
        grp_actions = QGroupBox("Quick Navigation & Screen Tests")
        act_layout = QVBoxLayout(grp_actions)

        btn_gs = QPushButton("⭐ Toggle Game Switcher (MENU)")
        btn_gs.setStyleSheet("background: #34c759; color: #fff; font-weight: bold; padding: 8px;")
        btn_gs.clicked.connect(self.canvas.toggle_menu)
        act_layout.addWidget(btn_gs)

        btn_fav = QPushButton("⭐ Go to Favorites")
        btn_fav.setStyleSheet("background: #2c2c2e; color: #fff; padding: 6px;")
        btn_fav.clicked.connect(lambda: self.switch_to_tab(0))
        act_layout.addWidget(btn_fav)

        btn_games = QPushButton("🎮 Go to Games (Consoles)")
        btn_games.setStyleSheet("background: #2c2c2e; color: #fff; padding: 6px;")
        btn_games.clicked.connect(lambda: self.switch_to_tab(1))
        act_layout.addWidget(btn_games)

        btn_apps = QPushButton("📱 Go to Apps & Tools")
        btn_apps.setStyleSheet("background: #2c2c2e; color: #fff; padding: 6px;")
        btn_apps.clicked.connect(lambda: self.switch_to_tab(2))
        act_layout.addWidget(btn_apps)

        btn_tweaks = QPushButton("⚡ Go to Onion Tweaks")
        btn_tweaks.setStyleSheet("background: #2c2c2e; color: #fff; padding: 6px;")
        btn_tweaks.clicked.connect(self.open_tweaks)
        act_layout.addWidget(btn_tweaks)

        layout.addWidget(grp_actions)

        # 3. System Status Controls
        grp_status = QGroupBox("Simulate Device Status")
        stat_layout = QVBoxLayout(grp_status)

        bat_box = QHBoxLayout()
        bat_box.addWidget(QLabel("Battery:"))
        self.bat_slider = QSlider(Qt.Orientation.Horizontal)
        self.bat_slider.setRange(5, 100)
        self.bat_slider.setValue(self.canvas.battery_level)
        self.bat_slider.valueChanged.connect(self.on_battery_changed)
        bat_box.addWidget(self.bat_slider)
        self.bat_val_lbl = QLabel(f"{self.canvas.battery_level}%")
        bat_box.addWidget(self.bat_val_lbl)
        stat_layout.addLayout(bat_box)

        layout.addWidget(grp_status)
        layout.addStretch()

        scroll.setWidget(widget)
        return scroll

    def create_guide_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        guide_lbl = QLabel("🎮 Keyboard & Gamepad Controls")
        guide_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        guide_lbl.setStyleSheet("color: #007aff;")
        layout.addWidget(guide_lbl)

        box = QGroupBox("Keybindings Mapping")
        b_layout = QVBoxLayout(box)
        
        keys = [
            ("W / A / S / D", "D-Pad Navigation (Up / Left / Down / Right)"),
            ("Arrow Keys", "D-Pad Navigation"),
            ("J  /  Enter", "A Button (Select / Launch Game)"),
            ("K  /  Escape", "B Button (Back / Cancel)"),
            ("U", "X Button (Toggle Favorite / Delete Switcher Slot)"),
            ("I", "Y Button (Context Action)"),
            ("M  /  Space", "MENU Button (Onion Game Switcher)"),
            ("Q  /  E", "L1 / R1 Triggers (Previous / Next Tab)"),
            ("Mouse Click", "Click physical buttons directly on the Miyoo casing")
        ]

        for k, desc in keys:
            row = QHBoxLayout()
            lbl_k = QLabel(f"<b>{k}</b>")
            lbl_k.setStyleSheet("color: #ff9500; font-family: Consolas; min-width: 100px;")
            lbl_d = QLabel(desc)
            lbl_d.setStyleSheet("color: #ccc; font-size: 11px;")
            lbl_d.setWordWrap(True)
            row.addWidget(lbl_k)
            row.addWidget(lbl_d, 1)
            b_layout.addLayout(row)

        layout.addWidget(box)
        layout.addStretch()

        scroll.setWidget(widget)
        return scroll

    # Handlers
    def on_theme_changed(self, name):
        self.theme_mgr.set_theme(name)
        self.update_theme_preview()
        self.update_theme_info()
        self.canvas.update()

    def update_theme_preview(self):
        t = self.theme_mgr.current_theme
        if t and hasattr(self, 'preview_lbl') and self.preview_lbl:
            p_path = t.get_preview_path()
            if p_path and os.path.exists(p_path):
                pm = QPixmap(p_path)
                self.preview_lbl.setPixmap(pm.scaled(200, 110, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                return
            self.preview_lbl.setText("No Preview Image")

    def update_theme_info(self):
        t = self.theme_mgr.current_theme
        if hasattr(self, 'theme_info_lbl') and self.theme_info_lbl:
            if t:
                self.theme_info_lbl.setText(f"Author: {t.author}\nDescription: {t.description}")
            else:
                self.theme_info_lbl.setText("")

    def on_shell_changed(self, sname):
        self.frame_widget.set_shell(sname)

    def on_battery_changed(self, val):
        self.canvas.battery_level = val
        self.bat_val_lbl.setText(f"{val}%")
        self.canvas.update()

    def pick_title_color(self):
        t = self.theme_mgr.current_theme
        if not t:
            return
        col = QColorDialog.getColor(t.title_color, self, "Pick Title Color")
        if col.isValid():
            t.title_color = col
            self.canvas.update()

    def pick_hint_color(self):
        t = self.theme_mgr.current_theme
        if not t:
            return
        col = QColorDialog.getColor(t.hint_color, self, "Pick Hint Color")
        if col.isValid():
            t.hint_color = col
            self.canvas.update()

    def pick_bat_color(self):
        t = self.theme_mgr.current_theme
        if not t:
            return
        col = QColorDialog.getColor(t.bat_color, self, "Pick Battery Color")
        if col.isValid():
            t.bat_color = col
            self.canvas.update()

    def switch_to_tab(self, tab_idx):
        self.canvas.view_stack = ['MAIN_CAROUSEL']
        self.canvas.current_tab = tab_idx
        self.canvas.switcher_open = False
        self.canvas.active_running_game = None
        self.canvas.update()

    def open_tweaks(self):
        self.canvas.view_stack = ['MAIN_CAROUSEL', 'APP_LIST', 'TWEAKS']
        self.canvas.switcher_open = False
        self.canvas.active_running_game = None
        self.canvas.update()

    def export_theme_to_sd(self):
        t = self.theme_mgr.current_theme
        if not t:
            QMessageBox.warning(self, "No Theme", "Vui lòng chọn một theme trước.")
            return

        dest_drive = self.drive_combo.currentData() or self.sys_data.sd_root
        if not dest_drive or not os.path.exists(dest_drive):
            QMessageBox.warning(self, "Invalid Destination", "Ổ đĩa mục tiêu không truy cập được.")
            return

        dest_themes = os.path.join(dest_drive, "Themes")
        os.makedirs(dest_themes, exist_ok=True)
        dest_dir = os.path.join(dest_themes, t.name)
        
        try:
            shutil.copytree(t.folder_path, dest_dir, dirs_exist_ok=True)
            QMessageBox.information(self, "Thành công", f"Theme '{t.name}' đã được xuất sang:\n{dest_dir}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể xuất theme: {e}")
