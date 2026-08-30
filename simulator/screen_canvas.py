import os
import datetime
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QPixmap, QLinearGradient, QRadialGradient
from PyQt6.QtCore import Qt, QRectF, QPointF, QTimer
from simulator.i18n import tr, add_listener

class ScreenCanvas(QWidget):
    def __init__(self, theme_mgr, system_data, parent=None):
        super().__init__(parent)
        self.theme_mgr = theme_mgr
        self.sys_data = system_data
        
        # 640x480 Native Miyoo Resolution
        self.setFixedSize(640, 480)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Navigation States
        # Views: 'MAIN_CAROUSEL', 'EMU_LIST', 'GAME_LIST', 'APP_LIST', 'EXPERT_LIST', 'SETTINGS_LIST', 'TWEAKS', 'ACTIVITY', 'GAME_RUNNING'
        self.view_stack = ['MAIN_CAROUSEL']
        self.current_tab = 1  # 0: Fav, 1: Games, 2: Apps, 3: Expert, 4: Settings
        
        self.selected_emu_idx = 0
        self.selected_game_idx = 0
        self.selected_app_idx = 0
        self.selected_expert_idx = 0
        self.selected_setting_idx = 0
        self.selected_tweak_idx = 0
        
        self.active_running_game = None
        
        # Game Switcher Overlay
        self.switcher_open = False
        self.switcher_idx = 0

        # Status indicators
        self.battery_level = 96
        self.is_charging = False
        self.wifi_strength = 4
        self.volume = 14
        self.brightness = 8
        self.game_frame_count = 0
        
        # Real-time clock & animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer_tick)
        self.timer.start(50)
        
        add_listener(self.update)

    @property
    def tweaks_list(self):
        return [
            {"name": tr("tweak_quicksave"), "val": tr("tweak_quicksave_val"), "desc": tr("tweak_quicksave_desc"), "icon": "save"},
            {"name": tr("tweak_menu_tap"), "val": tr("tweak_menu_tap_val"), "desc": tr("tweak_menu_tap_desc"), "icon": "menu_btn"},
            {"name": tr("tweak_menu_hold"), "val": tr("tweak_menu_hold_val"), "desc": tr("tweak_menu_hold_desc"), "icon": "power"},
            {"name": tr("tweak_cpu"), "val": tr("tweak_cpu_val"), "desc": tr("tweak_cpu_desc"), "icon": "cpu"},
            {"name": tr("tweak_web"), "val": tr("tweak_web_val"), "desc": tr("tweak_web_desc"), "icon": "web"},
            {"name": tr("tweak_samba"), "val": tr("tweak_samba_val"), "desc": tr("tweak_samba_desc"), "icon": "network"},
            {"name": tr("tweak_cloud"), "val": tr("tweak_cloud_val"), "desc": tr("tweak_cloud_desc"), "icon": "cloud"},
            {"name": tr("tweak_achieve"), "val": tr("tweak_achieve_val"), "desc": tr("tweak_achieve_desc"), "icon": "trophy"},
            {"name": tr("tweak_led"), "val": tr("tweak_led_val"), "desc": tr("tweak_led_desc"), "icon": "led"}
        ]

    @property
    def settings_list(self):
        return [
            {"name": tr("setting_theme"), "val": tr("setting_theme_val"), "icon": "theme"},
            {"name": tr("setting_wifi"), "val": tr("setting_wifi_val"), "icon": "wifi"},
            {"name": tr("setting_brightness"), "val": tr("setting_brightness_val"), "icon": "brightness"},
            {"name": tr("setting_volume"), "val": tr("setting_volume_val"), "icon": "volume"},
            {"name": tr("setting_cpu"), "val": tr("setting_cpu_val"), "icon": "cpu"},
            {"name": tr("setting_rumble"), "val": tr("setting_rumble_val"), "icon": "rumble"},
            {"name": tr("setting_clock"), "val": tr("setting_clock_val"), "icon": "clock"},
            {"name": tr("setting_storage"), "val": tr("setting_storage_val"), "icon": "sdcard"},
            {"name": tr("setting_language"), "val": tr("setting_language_val"), "icon": "language"},
            {"name": tr("setting_about"), "val": tr("setting_about_val"), "icon": "about"}
        ]

    def on_timer_tick(self):
        if self.current_view == 'GAME_RUNNING':
            self.game_frame_count += 1
        self.update()

    @property
    def current_view(self):
        return self.view_stack[-1]

    def push_view(self, view_name):
        self.view_stack.append(view_name)
        self.theme_mgr.play_sfx("select")
        self.update()

    def pop_view(self):
        if len(self.view_stack) > 1:
            self.view_stack.pop()
            self.theme_mgr.play_sfx("back")
            self.update()
            return True
        return False

    # Input Handlers
    def nav_up(self):
        if self.switcher_open:
            return
        v = self.current_view
        if v == 'EMU_LIST':
            self.selected_emu_idx = (self.selected_emu_idx - 1) % len(self.sys_data.emulators)
        elif v == 'GAME_LIST':
            cur_emu = self.sys_data.emulators[self.selected_emu_idx]
            if cur_emu.games:
                self.selected_game_idx = (self.selected_game_idx - 1) % len(cur_emu.games)
        elif v == 'APP_LIST':
            self.selected_app_idx = (self.selected_app_idx - 1) % len(self.sys_data.apps)
        elif v == 'EXPERT_LIST':
            self.selected_expert_idx = (self.selected_expert_idx - 1) % len(self.sys_data.expert_emulators)
        elif v == 'SETTINGS_LIST':
            self.selected_setting_idx = (self.selected_setting_idx - 1) % len(self.settings_list)
        elif v == 'TWEAKS':
            self.selected_tweak_idx = (self.selected_tweak_idx - 1) % len(self.tweaks_list)
        self.theme_mgr.play_sfx("change")
        self.update()

    def nav_down(self):
        if self.switcher_open:
            return
        v = self.current_view
        if v == 'EMU_LIST':
            self.selected_emu_idx = (self.selected_emu_idx + 1) % len(self.sys_data.emulators)
        elif v == 'GAME_LIST':
            cur_emu = self.sys_data.emulators[self.selected_emu_idx]
            if cur_emu.games:
                self.selected_game_idx = (self.selected_game_idx + 1) % len(cur_emu.games)
        elif v == 'APP_LIST':
            self.selected_app_idx = (self.selected_app_idx + 1) % len(self.sys_data.apps)
        elif v == 'EXPERT_LIST':
            self.selected_expert_idx = (self.selected_expert_idx + 1) % len(self.sys_data.expert_emulators)
        elif v == 'SETTINGS_LIST':
            self.selected_setting_idx = (self.selected_setting_idx + 1) % len(self.settings_list)
        elif v == 'TWEAKS':
            self.selected_tweak_idx = (self.selected_tweak_idx + 1) % len(self.tweaks_list)
        self.theme_mgr.play_sfx("change")
        self.update()

    def nav_left(self):
        if self.switcher_open:
            self.switcher_idx = (self.switcher_idx - 1) % len(self.sys_data.switcher_slots)
            self.theme_mgr.play_sfx("change")
            self.update()
            return
            
        if self.current_view == 'MAIN_CAROUSEL':
            self.current_tab = (self.current_tab - 1) % 5
            self.theme_mgr.play_sfx("change")
            self.update()
        elif self.current_view == 'GAME_LIST':
            cur_emu = self.sys_data.emulators[self.selected_emu_idx]
            if cur_emu.games:
                self.selected_game_idx = max(0, self.selected_game_idx - 6)
                self.theme_mgr.play_sfx("change")
                self.update()

    def nav_right(self):
        if self.switcher_open:
            self.switcher_idx = (self.switcher_idx + 1) % len(self.sys_data.switcher_slots)
            self.theme_mgr.play_sfx("change")
            self.update()
            return

        if self.current_view == 'MAIN_CAROUSEL':
            self.current_tab = (self.current_tab + 1) % 5
            self.theme_mgr.play_sfx("change")
            self.update()
        elif self.current_view == 'GAME_LIST':
            cur_emu = self.sys_data.emulators[self.selected_emu_idx]
            if cur_emu.games:
                self.selected_game_idx = min(len(cur_emu.games) - 1, self.selected_game_idx + 6)
                self.theme_mgr.play_sfx("change")
                self.update()

    def press_a(self):
        if self.switcher_open:
            self.switcher_open = False
            if self.sys_data.switcher_slots and 0 <= self.switcher_idx < len(self.sys_data.switcher_slots):
                slot = self.sys_data.switcher_slots[self.switcher_idx]
                self.active_running_game = slot.title
                if self.current_view != 'GAME_RUNNING':
                    self.push_view('GAME_RUNNING')
                else:
                    self.update()
            self.theme_mgr.play_sfx("select")
            return

        v = self.current_view
        if v == 'MAIN_CAROUSEL':
            if self.current_tab == 0:  # Favs
                self.push_view('EMU_LIST')
            elif self.current_tab == 1:  # Games
                self.push_view('EMU_LIST')
            elif self.current_tab == 2:  # Apps
                self.push_view('APP_LIST')
            elif self.current_tab == 3:  # Expert
                self.push_view('EXPERT_LIST')
            elif self.current_tab == 4:  # Settings
                self.push_view('SETTINGS_LIST')
        elif v == 'EMU_LIST':
            self.selected_game_idx = 0
            self.push_view('GAME_LIST')
        elif v == 'APP_LIST':
            app = self.sys_data.apps[self.selected_app_idx]
            if app.app_id == 'tweaks':
                self.push_view('TWEAKS')
            elif app.app_id == 'activity':
                self.push_view('ACTIVITY')
            else:
                self.theme_mgr.play_sfx("select")
        elif v == 'SETTINGS_LIST':
            if self.selected_setting_idx == 5:  # Tweaks
                self.push_view('TWEAKS')
            else:
                self.theme_mgr.play_sfx("select")
        elif v == 'GAME_LIST':
            cur_emu = self.sys_data.emulators[self.selected_emu_idx]
            if cur_emu.games:
                g = cur_emu.games[self.selected_game_idx]
                self.active_running_game = f"{g.title} ({cur_emu.name})"
                self.push_view('GAME_RUNNING')

    def press_b(self):
        if self.switcher_open:
            self.switcher_open = False
            self.theme_mgr.play_sfx("back")
            self.update()
            return
        self.pop_view()

    def press_x(self):
        if self.current_view == 'GAME_LIST':
            cur_emu = self.sys_data.emulators[self.selected_emu_idx]
            if cur_emu.games:
                g = cur_emu.games[self.selected_game_idx]
                g.is_favorite = not g.is_favorite
                self.theme_mgr.play_sfx("select")
                self.update()

    def press_y(self):
        self.theme_mgr.play_sfx("select")

    def toggle_menu(self):
        self.switcher_open = not self.switcher_open
        if self.switcher_open:
            self.theme_mgr.play_sfx("select")
        else:
            self.theme_mgr.play_sfx("back")
        self.update()

    # Painting / Rendering
    def paintEvent(self, event):
        painter = QPainter(self)
        self.draw_ui(painter)

    def draw_ui(self, painter):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        sx = max(1, self.width()) / 640.0
        sy = max(1, self.height()) / 480.0
        painter.scale(sx, sy)
        
        theme = self.theme_mgr.current_theme
        
        # 1. Background
        bg_pix = theme.get_pixmap("background.png") if theme else None
        if bg_pix and not bg_pix.isNull():
            painter.drawPixmap(0, 0, 640, 480, bg_pix)
            # Soft dark frosted scrim so UI elements and icons have maximum contrast
            painter.fillRect(0, 0, 640, 480, QColor(5, 8, 16, 135))
        else:
            grad = QLinearGradient(0, 0, 640, 480)
            grad.setColorAt(0.0, QColor("#04070e"))
            grad.setColorAt(0.5, QColor("#090e1c"))
            grad.setColorAt(1.0, QColor("#050a14"))
            painter.fillRect(0, 0, 640, 480, grad)

        # 2. View Content
        boot_mode = self.sys_data.boot_diag.boot_mode
        if boot_mode == 'NO_SD':
            self.draw_no_sd_screen(painter)
            return
            
        if self.current_view == 'MAIN_CAROUSEL':
            if boot_mode == 'STOCK_OS':
                self.draw_stock_main_menu(painter)
            else:
                self.draw_main_carousel(painter, theme)
        elif self.current_view == 'EMU_LIST':
            self.draw_emu_list(painter, theme)
        elif self.current_view == 'GAME_LIST':
            self.draw_game_list(painter, theme)
        elif self.current_view == 'APP_LIST':
            self.draw_app_list(painter, theme)
        elif self.current_view == 'EXPERT_LIST':
            self.draw_expert_list(painter, theme)
        elif self.current_view == 'SETTINGS_LIST':
            self.draw_settings_list(painter, theme)
        elif self.current_view == 'TWEAKS':
            self.draw_tweaks_view(painter, theme)
        elif self.current_view == 'ACTIVITY':
            self.draw_activity_view(painter, theme)
        elif self.current_view == 'GAME_RUNNING':
            self.draw_game_running(painter, theme)

        # 3. Top Status Bar & Bottom Bar (Only when not in Game Switcher or Game Running)
        if not self.switcher_open and self.current_view != 'GAME_RUNNING':
            self.draw_topbar(painter, theme)
            self.draw_bottom_bar(painter, theme)

        # 4. Game Switcher Overlay (Solid overlay on top)
        if self.switcher_open:
            if boot_mode in ['CUSTOM_OS', 'ONION_OS']:
                self.draw_game_switcher(painter, theme)
            else:
                self.draw_stock_menu_dialog(painter)

    def draw_topbar(self, painter, theme):
        # Frosted glass top bar
        painter.fillRect(0, 0, 640, 36, QColor(15, 23, 42, 220))
        painter.fillRect(0, 35, 640, 1, QColor(0, 240, 255, 100))

        # Time
        now = datetime.datetime.now().strftime("%H:%M")
        painter.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        painter.setPen(QPen(QColor("#FFFFFF")))
        painter.drawText(QRectF(25, 6, 80, 24), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, now)

        # Logo / OS Title
        painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Black))
        painter.setPen(QPen(QColor("#00f0ff")))
        painter.drawText(QRectF(0, 6, 640, 24), Qt.AlignmentFlag.AlignCenter, "⚡ KAYZIT BASIC")

        # Battery & Wi-Fi
        bat_level = self.battery_level
        bat_col = QColor("#10b981") if bat_level > 20 else QColor("#ef4444")
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.setPen(QPen(bat_col))
        painter.drawText(QRectF(520, 6, 50, 24), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, f"{bat_level}%")

        # Battery Icon
        bx, by = 576, 12
        painter.setPen(QPen(QColor("#cbd5e1"), 1.2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(bx, by, 24, 12, 2, 2)
        painter.fillRect(bx + 25, by + 3, 2, 6, QColor("#cbd5e1"))
        
        fill_w = max(2, int(20 * (bat_level / 100.0)))
        painter.fillRect(bx + 2, by + 2, fill_w, 8, bat_col)

    def draw_bottom_bar(self, painter, theme):
        # Frosted glass bottom dock
        painter.fillRect(0, 442, 640, 38, QColor(15, 23, 42, 230))
        painter.fillRect(0, 442, 640, 1, QColor(255, 255, 255, 30))

        v = self.current_view
        boot_mode = self.sys_data.boot_diag.boot_mode
        if boot_mode == 'STOCK_OS':
            hints = [("A", tr("ui_nav_select")), ("B", tr("ui_nav_back")), ("💡", "Stock Mode: No SD")]
        elif v == 'MAIN_CAROUSEL':
            hints = [("A", tr("ui_nav_open")), ("MENU", tr("ui_nav_switcher")), ("L/R", tr("ui_nav_tabs"))]
        elif v == 'GAME_LIST':
            hints = [("A", "Play"), ("B", tr("ui_nav_back")), ("X", "Star"), ("MENU", tr("ui_nav_switcher"))]
        elif v == 'TWEAKS':
            hints = [("A", tr("ui_nav_toggle")), ("B", tr("ui_nav_back"))]
        else:
            hints = [("A", tr("ui_nav_select")), ("B", tr("ui_nav_back")), ("MENU", tr("ui_nav_switcher"))]

        hx = 25
        for btn, label in hints:
            btn_w = 26 if len(btn) <= 2 else (50 if len(btn) <= 4 else 60)
            painter.setPen(QPen(QColor(0, 240, 255, 120), 1))
            painter.setBrush(QColor(30, 41, 59, 200))
            painter.drawRoundedRect(hx, 450, btn_w, 22, 5, 5)
            
            painter.setPen(QPen(QColor("#00f0ff")))
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            painter.drawText(QRectF(hx, 450, btn_w, 22), Qt.AlignmentFlag.AlignCenter, btn)
            
            painter.setPen(QPen(QColor("#cbd5e1")))
            painter.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
            painter.drawText(QRectF(hx + btn_w + 6, 450, 95, 22), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, label)
            hx += btn_w + 105

    def draw_main_carousel(self, painter, theme):
        tabs = [
            (tr("tab_name_favorites"), "favorites", tr("tab_sub_favorites")),
            (tr("tab_name_games"), "games", tr("tab_sub_games")),
            (tr("tab_name_apps"), "apps", tr("tab_sub_apps")),
            (tr("tab_name_expert"), "expert", tr("tab_sub_expert")),
            (tr("tab_name_settings"), "settings", tr("tab_sub_settings"))
        ]

        title, raw_name, subtitle = tabs[self.current_tab]

        # 1. Header Title & Subtitle
        painter.setPen(QPen(QColor("#00f0ff")))
        painter.setFont(QFont("Segoe UI", 22, QFont.Weight.Black))
        painter.drawText(QRectF(0, 48, 640, 32), Qt.AlignmentFlag.AlignCenter, title.upper())

        painter.setPen(QPen(QColor("#94a3b8")))
        painter.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        painter.drawText(QRectF(0, 80, 640, 22), Qt.AlignmentFlag.AlignCenter, subtitle)

        center_x = 320

        # 2. Render 3D Cards for Carousel Items
        for i, (tab_name, t_icon_name, _) in enumerate(tabs):
            offset = i - self.current_tab
            is_active = (i == self.current_tab)

            # Resolve 3D icon
            icon_path = self.theme_mgr.get_icon_path(t_icon_name, is_app=True)
            pix = None
            if icon_path and os.path.exists(icon_path):
                pix = QPixmap(icon_path)
            if not pix or pix.isNull():
                pix = theme.get_pixmap(f"{t_icon_name}.png") if theme else None

            if is_active:
                # Active Center 3D Glass Hero Card
                card_w = 200
                card_h = 210
                cx = center_x - (card_w // 2)
                cy = 108

                # Drop Shadow
                sh_grad = QRadialGradient(center_x, cy + card_h + 4, 110)
                sh_grad.setColorAt(0.0, QColor(0, 0, 0, 180))
                sh_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(sh_grad)
                painter.drawEllipse(QRectF(cx - 10, cy + card_h - 10, card_w + 20, 24))

                # 3D Glass Card Body
                c_grad = QLinearGradient(cx, cy, cx + card_w, cy + card_h)
                c_grad.setColorAt(0.0, QColor(30, 41, 59, 235))
                c_grad.setColorAt(1.0, QColor(15, 23, 42, 245))
                
                painter.setPen(QPen(QColor("#00f0ff"), 1.8))
                painter.setBrush(c_grad)
                painter.drawRoundedRect(QRectF(cx, cy, card_w, card_h), 16, 16)

                # Specular Glare Reflection at Top
                g_grad = QLinearGradient(cx, cy, cx, cy + 60)
                g_grad.setColorAt(0.0, QColor(255, 255, 255, 70))
                g_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(g_grad)
                painter.drawRoundedRect(QRectF(cx + 2, cy + 2, card_w - 4, 55), 14, 14)

                # 3D Icon Image
                icon_size = 96
                ix = cx + (card_w - icon_size) // 2
                iy = cy + 18
                if pix and not pix.isNull():
                    painter.drawPixmap(ix, iy, icon_size, icon_size, pix.scaled(icon_size, icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

                # Title inside Card
                painter.setPen(QPen(QColor("#FFFFFF")))
                painter.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
                painter.drawText(QRectF(cx + 10, cy + 124, card_w - 20, 24), Qt.AlignmentFlag.AlignCenter, tab_name)

                # Action Capsule Pill
                pill_w, pill_h = 120, 24
                px = cx + (card_w - pill_w) // 2
                py = cy + 158
                p_grad = QLinearGradient(px, py, px + pill_w, py + pill_h)
                p_grad.setColorAt(0.0, QColor("#0284c7"))
                p_grad.setColorAt(1.0, QColor("#00f0ff"))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(p_grad)
                painter.drawRoundedRect(QRectF(px, py, pill_w, pill_h), 12, 12)

                painter.setPen(QPen(QColor("#0f172a")))
                painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Black))
                painter.drawText(QRectF(px, py, pill_w, pill_h), Qt.AlignmentFlag.AlignCenter, tr("ui_press_open"))

            elif -2 <= offset <= 2:
                # Flanking Side Cards
                card_w = 115
                card_h = 135
                cx = center_x + (offset * 180) - (card_w // 2)
                cy = 145

                painter.setOpacity(0.45)
                painter.setPen(QPen(QColor(255, 255, 255, 40), 1))
                painter.setBrush(QColor(15, 23, 42, 180))
                painter.drawRoundedRect(QRectF(cx, cy, card_w, card_h), 12, 12)

                icon_size = 54
                ix = cx + (card_w - icon_size) // 2
                iy = cy + 18
                if pix and not pix.isNull():
                    painter.drawPixmap(ix, iy, icon_size, icon_size, pix.scaled(icon_size, icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

                painter.setPen(QPen(QColor("#e2e8f0")))
                painter.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
                painter.drawText(QRectF(cx + 5, cy + 82, card_w - 10, 22), Qt.AlignmentFlag.AlignCenter, tab_name)
                painter.setOpacity(1.0)

        # 3. Bottom Pagination Indicator (Capsule + Dots)
        dot_y = 338
        total_w = len(tabs) * 20 + 16
        start_x = center_x - (total_w // 2)

        cur_x = start_x
        for i in range(len(tabs)):
            if i == self.current_tab:
                # Glowing capsule
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor("#00f0ff"))
                painter.drawRoundedRect(QRectF(cur_x, dot_y, 22, 6), 3, 3)
                cur_x += 28
            else:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(255, 255, 255, 70))
                painter.drawEllipse(QRectF(cur_x, dot_y, 6, 6))
                cur_x += 16

    def draw_emu_list(self, painter, theme):
        painter.setPen(QPen(QColor("#00f0ff")))
        painter.setFont(QFont("Segoe UI", 16, QFont.Weight.Black))
        painter.drawText(QRectF(25, 46, 350, 28), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "🎮 " + tr("view_title_consoles"))

        list_x = 25
        list_y = 78
        item_h = 48
        visible_count = 7
        
        start_idx = max(0, self.selected_emu_idx - 3)
        if start_idx + visible_count > len(self.sys_data.emulators):
            start_idx = max(0, len(self.sys_data.emulators) - visible_count)
        end_idx = min(len(self.sys_data.emulators), start_idx + visible_count)

        for i in range(start_idx, end_idx):
            emu = self.sys_data.emulators[i]
            y = list_y + (i - start_idx) * item_h
            is_selected = (i == self.selected_emu_idx)

            if is_selected:
                painter.setPen(QPen(QColor("#00f0ff"), 1.5))
                painter.setBrush(QColor(30, 41, 59, 220))
                painter.drawRoundedRect(list_x, y, 350, item_h - 4, 10, 10)
                painter.fillRect(list_x, y + 6, 4, item_h - 16, QColor("#00f0ff"))
                painter.setPen(QPen(QColor("#FFFFFF")))
            else:
                painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
                painter.setBrush(QColor(15, 23, 42, 160))
                painter.drawRoundedRect(list_x, y, 350, item_h - 4, 10, 10)
                painter.setPen(QPen(QColor("#cbd5e1")))

            icon_path = self.theme_mgr.get_icon_path(emu.icon_id)
            if icon_path and os.path.exists(icon_path):
                pm = QPixmap(icon_path)
                painter.drawPixmap(list_x + 10, y + 6, 32, 32, pm)

            painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold if is_selected else QFont.Weight.DemiBold))
            painter.drawText(QRectF(list_x + 50, y, 220, item_h - 4), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, emu.name)
            
            painter.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
            painter.setPen(QPen(QColor("#00f0ff") if is_selected else QColor("#94a3b8")))
            painter.drawText(QRectF(list_x + 265, y, 75, item_h - 4), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, f"{len(emu.games)} roms")

        cur_emu = self.sys_data.emulators[self.selected_emu_idx]
        card_x = 395
        card_y = 78
        card_w = 220
        card_h = 336
        
        # 3D Glass Preview Card
        painter.setPen(QPen(QColor("#00f0ff"), 1.2))
        c_grad = QLinearGradient(card_x, card_y, card_x + card_w, card_y + card_h)
        c_grad.setColorAt(0.0, QColor(30, 41, 59, 230))
        c_grad.setColorAt(1.0, QColor(15, 23, 42, 245))
        painter.setBrush(c_grad)
        painter.drawRoundedRect(card_x, card_y, card_w, card_h, 14, 14)

        big_icon_path = self.theme_mgr.get_icon_path(cur_emu.icon_id)
        if big_icon_path and os.path.exists(big_icon_path):
            bpm = QPixmap(big_icon_path)
            painter.drawPixmap(card_x + 70, card_y + 25, 80, 80, bpm)

        painter.setPen(QPen(QColor("#FFFFFF")))
        painter.setFont(QFont("Segoe UI", 13, QFont.Weight.Black))
        painter.drawText(QRectF(card_x + 10, card_y + 125, card_w - 20, 36), Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, cur_emu.name)

        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        painter.setPen(QPen(QColor("#94a3b8")))
        painter.drawText(QRectF(card_x + 10, card_y + 180, card_w - 20, 20), Qt.AlignmentFlag.AlignCenter, f"System Code: {cur_emu.code}")
        painter.drawText(QRectF(card_x + 10, card_y + 210, card_w - 20, 20), Qt.AlignmentFlag.AlignCenter, f"Total ROMs: {len(cur_emu.games)}")
        painter.drawText(QRectF(card_x + 10, card_y + 240, card_w - 20, 20), Qt.AlignmentFlag.AlignCenter, "Engine: Kayzit Libretro")

    def draw_game_list(self, painter, theme):
        cur_emu = self.sys_data.emulators[self.selected_emu_idx]
        
        painter.setPen(QPen(QColor("#00f0ff")))
        painter.setFont(QFont("Segoe UI", 16, QFont.Weight.Black))
        painter.drawText(QRectF(25, 46, 350, 28), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, f"{cur_emu.name} ({len(cur_emu.games)})")

        list_x = 25
        list_y = 78
        item_h = 48
        visible_count = 7

        if not cur_emu.games:
            painter.setPen(QPen(QColor("#94a3b8")))
            painter.setFont(QFont("Segoe UI", 13, QFont.Weight.Normal))
            painter.drawText(QRectF(30, 120, 340, 40), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "No ROMs found in this folder.")
            return

        start_idx = max(0, self.selected_game_idx - 3)
        if start_idx + visible_count > len(cur_emu.games):
            start_idx = max(0, len(cur_emu.games) - visible_count)
        end_idx = min(len(cur_emu.games), start_idx + visible_count)

        for i in range(start_idx, end_idx):
            g = cur_emu.games[i]
            y = list_y + (i - start_idx) * item_h
            is_selected = (i == self.selected_game_idx)

            if is_selected:
                painter.setPen(QPen(QColor("#00f0ff"), 1.5))
                painter.setBrush(QColor(30, 41, 59, 220))
                painter.drawRoundedRect(list_x, y, 350, item_h - 4, 10, 10)
                painter.fillRect(list_x, y + 6, 4, item_h - 16, QColor("#00f0ff"))
                painter.setPen(QPen(QColor("#FFFFFF")))
            else:
                painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
                painter.setBrush(QColor(15, 23, 42, 160))
                painter.drawRoundedRect(list_x, y, 350, item_h - 4, 10, 10)
                painter.setPen(QPen(QColor("#cbd5e1")))

            if g.is_favorite:
                painter.setPen(QPen(QColor("#fbbf24")))
                painter.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
                painter.drawText(QRectF(list_x + 8, y, 20, item_h - 4), Qt.AlignmentFlag.AlignCenter, "★")
            else:
                painter.setPen(QPen(QColor("#64748b")))
                painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Normal))
                painter.drawText(QRectF(list_x + 8, y, 20, item_h - 4), Qt.AlignmentFlag.AlignCenter, "•")

            painter.setPen(QPen(QColor("#FFFFFF") if is_selected else QColor("#cbd5e1")))
            painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold if is_selected else QFont.Weight.DemiBold))
            
            disp_title = g.title if len(g.title) <= 28 else g.title[:26] + "..."
            painter.drawText(QRectF(list_x + 30, y, 310, item_h - 4), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, disp_title)

        cur_game = cur_emu.games[self.selected_game_idx]
        card_x = 395
        card_y = 78
        card_w = 220
        card_h = 336
        
        painter.setPen(QPen(QColor("#00f0ff"), 1.2))
        c_grad = QLinearGradient(card_x, card_y, card_x + card_w, card_y + card_h)
        c_grad.setColorAt(0.0, QColor(30, 41, 59, 230))
        c_grad.setColorAt(1.0, QColor(15, 23, 42, 245))
        painter.setBrush(c_grad)
        painter.drawRoundedRect(card_x, card_y, card_w, card_h, 14, 14)

        box_w = 140
        box_h = 160
        box_x = card_x + (card_w - box_w) // 2
        box_y = card_y + 15
        
        if cur_game.boxart and os.path.exists(cur_game.boxart):
            bpm = QPixmap(cur_game.boxart)
            painter.drawPixmap(box_x, box_y, box_w, box_h, bpm.scaled(box_w, box_h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            bgrad = QLinearGradient(box_x, box_y, box_x + box_w, box_y + box_h)
            bgrad.setColorAt(0.0, QColor("#1e293b"))
            bgrad.setColorAt(1.0, QColor("#0f172a"))
            painter.setPen(QPen(QColor("#00f0ff"), 1))
            painter.setBrush(bgrad)
            painter.drawRoundedRect(box_x, box_y, box_w, box_h, 8, 8)
            
            painter.setPen(QPen(QColor("#FFFFFF")))
            painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            painter.drawText(QRectF(box_x + 5, box_y + 20, box_w - 10, 120), Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, cur_game.title)

        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        painter.setPen(QPen(QColor("#94a3b8")))
        hours = cur_game.playtime_min // 60
        mins = cur_game.playtime_min % 60
        painter.drawText(QRectF(card_x + 10, card_y + 195, card_w - 20, 20), Qt.AlignmentFlag.AlignCenter, f"Playtime: {hours}h {mins}m")
        painter.drawText(QRectF(card_x + 10, card_y + 225, card_w - 20, 20), Qt.AlignmentFlag.AlignCenter, f"System: {cur_game.system_code}")
        painter.drawText(QRectF(card_x + 10, card_y + 255, card_w - 20, 20), Qt.AlignmentFlag.AlignCenter, "Save State: Slot 0 (Auto)")

    def draw_app_list(self, painter, theme):
        painter.setPen(QPen(QColor("#00f0ff")))
        painter.setFont(QFont("Segoe UI", 16, QFont.Weight.Black))
        painter.drawText(QRectF(25, 46, 350, 28), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "⚡ " + tr("view_title_apps"))

        list_x = 25
        list_y = 78
        item_h = 48
        visible_count = 7

        start_idx = max(0, self.selected_app_idx - 3)
        if start_idx + visible_count > len(self.sys_data.apps):
            start_idx = max(0, len(self.sys_data.apps) - visible_count)
        end_idx = min(len(self.sys_data.apps), start_idx + visible_count)

        for i in range(start_idx, end_idx):
            app = self.sys_data.apps[i]
            y = list_y + (i - start_idx) * item_h
            is_selected = (i == self.selected_app_idx)

            if is_selected:
                painter.setPen(QPen(QColor("#00f0ff"), 1.5))
                painter.setBrush(QColor(30, 41, 59, 220))
                painter.drawRoundedRect(list_x, y, 350, item_h - 4, 10, 10)
                painter.fillRect(list_x, y + 6, 4, item_h - 16, QColor("#00f0ff"))
                painter.setPen(QPen(QColor("#FFFFFF")))
            else:
                painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
                painter.setBrush(QColor(15, 23, 42, 160))
                painter.drawRoundedRect(list_x, y, 350, item_h - 4, 10, 10)
                painter.setPen(QPen(QColor("#cbd5e1")))

            icon_path = self.theme_mgr.get_icon_path(app.icon_id, is_app=True)
            if icon_path and os.path.exists(icon_path):
                pm = QPixmap(icon_path)
                painter.drawPixmap(list_x + 10, y + 6, 32, 32, pm)

            painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold if is_selected else QFont.Weight.DemiBold))
            painter.drawText(QRectF(list_x + 50, y, 290, item_h - 4), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, app.name)

        cur_app = self.sys_data.apps[self.selected_app_idx]
        card_x = 395
        card_y = 78
        card_w = 220
        card_h = 336
        
        painter.setPen(QPen(QColor("#00f0ff"), 1.2))
        c_grad = QLinearGradient(card_x, card_y, card_x + card_w, card_y + card_h)
        c_grad.setColorAt(0.0, QColor(30, 41, 59, 230))
        c_grad.setColorAt(1.0, QColor(15, 23, 42, 245))
        painter.setBrush(c_grad)
        painter.drawRoundedRect(card_x, card_y, card_w, card_h, 14, 14)

        big_icon_path = self.theme_mgr.get_icon_path(cur_app.icon_id, is_app=True)
        if big_icon_path and os.path.exists(big_icon_path):
            bpm = QPixmap(big_icon_path)
            painter.drawPixmap(card_x + 70, card_y + 25, 80, 80, bpm)

        painter.setPen(QPen(QColor("#FFFFFF")))
        painter.setFont(QFont("Segoe UI", 13, QFont.Weight.Black))
        painter.drawText(QRectF(card_x + 10, card_y + 120, card_w - 20, 30), Qt.AlignmentFlag.AlignCenter, cur_app.name)

        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Normal))
        painter.setPen(QPen(QColor("#94a3b8")))
        painter.drawText(QRectF(card_x + 15, card_y + 160, card_w - 30, 140), Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap, cur_app.description)

    def draw_expert_list(self, painter, theme):
        painter.setPen(QPen(QColor("#00f0ff")))
        painter.setFont(QFont("Segoe UI", 16, QFont.Weight.Black))
        painter.drawText(QRectF(25, 46, 350, 28), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "🕹️ " + tr("view_title_cores"))

        list_x = 25
        list_y = 78
        item_h = 48
        visible_count = 7

        start_idx = max(0, self.selected_expert_idx - 3)
        if start_idx + visible_count > len(self.sys_data.expert_emulators):
            start_idx = max(0, len(self.sys_data.expert_emulators) - visible_count)
        end_idx = min(len(self.sys_data.expert_emulators), start_idx + visible_count)

        for i in range(start_idx, end_idx):
            emu = self.sys_data.expert_emulators[i]
            y = list_y + (i - start_idx) * item_h
            is_selected = (i == self.selected_expert_idx)

            if is_selected:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(0, 122, 255, 180)))
                painter.drawRoundedRect(list_x, y, 350, item_h - 4, 8, 8)
                painter.setPen(QPen(QColor("#FFFFFF")))
            else:
                painter.setPen(QPen(theme.list_color if theme else QColor("#E0E0E0")))

            icon_path = self.theme_mgr.get_icon_path(emu.icon_id)
            if icon_path and os.path.exists(icon_path):
                pm = QPixmap(icon_path)
                painter.drawPixmap(list_x + 8, y + 7, 30, 30, pm)

            painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold if is_selected else QFont.Weight.Normal))
            painter.drawText(QRectF(list_x + 48, y, 290, item_h - 4), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, emu.name)

    def draw_settings_list(self, painter, theme):
        painter.setPen(QPen(QColor("#00f0ff")))
        painter.setFont(QFont("Segoe UI", 16, QFont.Weight.Black))
        painter.drawText(QRectF(25, 46, 350, 28), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "⚙️ " + tr("view_title_settings"))

        list_x = 25
        list_y = 78
        item_h = 42
        visible_count = 8

        start_idx = max(0, self.selected_setting_idx - 3)
        if start_idx + visible_count > len(self.settings_list):
            start_idx = max(0, len(self.settings_list) - visible_count)
        end_idx = min(len(self.settings_list), start_idx + visible_count)

        for i in range(start_idx, end_idx):
            item = self.settings_list[i]
            y = list_y + (i - start_idx) * item_h
            is_selected = (i == self.selected_setting_idx)

            if is_selected:
                painter.setPen(QPen(QColor("#00f0ff"), 1.5))
                painter.setBrush(QColor(30, 41, 59, 220))
                painter.drawRoundedRect(list_x, y, 590, item_h - 4, 8, 8)
                painter.fillRect(list_x, y + 4, 4, item_h - 12, QColor("#00f0ff"))
                painter.setPen(QPen(QColor("#FFFFFF")))
            else:
                painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
                painter.setBrush(QColor(15, 23, 42, 160))
                painter.drawRoundedRect(list_x, y, 590, item_h - 4, 8, 8)
                painter.setPen(QPen(QColor("#cbd5e1")))

            # Row 3D Icon
            icon_id = item.get("icon", "settings")
            icon_path = self.theme_mgr.get_icon_path(icon_id, is_app=True)
            if icon_path and os.path.exists(icon_path):
                pm = QPixmap(icon_path)
                painter.drawPixmap(list_x + 10, y + 5, 26, 26, pm)

            painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold if is_selected else QFont.Weight.DemiBold))
            painter.drawText(QRectF(list_x + 44, y, 260, item_h - 4), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, item["name"])

            painter.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
            painter.setPen(QPen(QColor("#00f0ff") if is_selected else QColor("#94a3b8")))
            painter.drawText(QRectF(list_x + 290, y, 285, item_h - 4), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, item["val"])

    def draw_tweaks_view(self, painter, theme):
        painter.setPen(QPen(QColor("#00f0ff")))
        painter.setFont(QFont("Segoe UI", 16, QFont.Weight.Black))
        painter.drawText(QRectF(25, 46, 350, 28), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "⚡ " + tr("view_title_tweaks"))

        list_x = 25
        list_y = 78
        item_h = 38
        visible_count = 8

        start_idx = max(0, self.selected_tweak_idx - 3)
        if start_idx + visible_count > len(self.tweaks_list):
            start_idx = max(0, len(self.tweaks_list) - visible_count)
        end_idx = min(len(self.tweaks_list), start_idx + visible_count)

        for i in range(start_idx, end_idx):
            item = self.tweaks_list[i]
            y = list_y + (i - start_idx) * item_h
            is_selected = (i == self.selected_tweak_idx)

            if is_selected:
                painter.setPen(QPen(QColor("#00f0ff"), 1.5))
                painter.setBrush(QColor(30, 41, 59, 220))
                painter.drawRoundedRect(list_x, y, 590, item_h - 4, 8, 8)
                painter.fillRect(list_x, y + 4, 4, item_h - 12, QColor("#00f0ff"))
                painter.setPen(QPen(QColor("#FFFFFF")))
            else:
                painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
                painter.setBrush(QColor(15, 23, 42, 160))
                painter.drawRoundedRect(list_x, y, 590, item_h - 4, 8, 8)
                painter.setPen(QPen(QColor("#cbd5e1")))

            # Tweak 3D Icon
            icon_id = item.get("icon", "cpu")
            icon_path = self.theme_mgr.get_icon_path(icon_id, is_app=True)
            if icon_path and os.path.exists(icon_path):
                pm = QPixmap(icon_path)
                painter.drawPixmap(list_x + 10, y + 4, 24, 24, pm)

            painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold if is_selected else QFont.Weight.DemiBold))
            painter.drawText(QRectF(list_x + 42, y, 290, item_h - 4), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, item["name"])

            painter.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
            val_col = QColor("#10b981") if ("Enabled" in item["val"] or "Active" in item["val"] or "1.4" in item["val"]) else QColor("#00f0ff")
            painter.setPen(QPen(val_col))
            painter.drawText(QRectF(list_x + 310, y, 265, item_h - 4), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, item["val"])

    def draw_activity_view(self, painter, theme):
        painter.setPen(QPen(theme.title_color if theme else QColor("#FFFFFF")))
        painter.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        painter.drawText(QRectF(25, 46, 350, 28), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "Activity Tracker (Play Statistics)")

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 140)))
        painter.drawRoundedRect(25, 78, 590, 70, 10, 10)

        painter.setPen(QPen(QColor("#FFFFFF")))
        painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        painter.drawText(QRectF(40, 85, 560, 24), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "Total Time Played: 78 hours 40 minutes")
        
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Normal))
        painter.setPen(QPen(QColor("#AAAAAA")))
        painter.drawText(QRectF(40, 112, 560, 24), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "Total Games Launched: 34 titles | Most Played: Pokémon Emerald")

        painter.setPen(QPen(QColor("#FFFFFF")))
        painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        painter.drawText(QRectF(25, 160, 300, 24), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "Most Played Games:")

        top_games = [
            ("Pokemon - Emerald Version (GBA)", "23h 40m", 95),
            ("Castlevania: Symphony of the Night (PS1)", "14h 50m", 60),
            ("Super Mario World (SNES)", "13h 00m", 52),
            ("Chrono Trigger (SNES)", "11h 00m", 44),
            ("Pokemon HeartGold (NDS)", "9h 30m", 38)
        ]

        for i, (gname, ptime, bar_pct) in enumerate(top_games):
            gy = 190 + i * 44
            painter.setPen(QPen(QColor("#DDDDDD")))
            painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Normal))
            painter.drawText(QRectF(25, gy, 350, 30), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, gname)
            
            painter.drawText(QRectF(380, gy, 80, 30), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, ptime)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(255, 255, 255, 30)))
            painter.drawRoundedRect(480, gy + 8, 130, 14, 4, 4)
            painter.setBrush(QBrush(QColor("#007aff")))
            painter.drawRoundedRect(480, gy + 8, int(1.3 * bar_pct), 14, 4, 4)

    def draw_game_running(self, painter, theme):
        painter.fillRect(0, 0, 640, 480, QColor("#000000"))

        gname = self.active_running_game or "Game Running"
        
        scan_step = 4
        painter.setPen(QPen(QColor(255, 255, 255, 12), 1))
        for y in range(0, 480, scan_step):
            painter.drawLine(0, y, 640, y)

        badge_w, badge_h = 440, 190
        bx = (640 - badge_w) // 2
        by = (480 - badge_h) // 2

        bgrad = QLinearGradient(bx, by, bx + badge_w, by + badge_h)
        bgrad.setColorAt(0, QColor("#141e30"))
        bgrad.setColorAt(1, QColor("#243b55"))
        painter.setPen(QPen(QColor("#00ffcc"), 2))
        painter.setBrush(QBrush(bgrad))
        painter.drawRoundedRect(bx, by, badge_w, badge_h, 16, 16)

        painter.setPen(QPen(QColor("#FFFFFF")))
        painter.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        painter.drawText(QRectF(bx + 15, by + 25, badge_w - 30, 50), Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, gname)

        painter.setPen(QPen(QColor("#4cd964")))
        painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Normal))
        fps = 60
        painter.drawText(QRectF(bx + 15, by + 85, badge_w - 30, 22), Qt.AlignmentFlag.AlignCenter, f"● Running at {fps} FPS | RetroArch Core: Active")

        painter.setPen(QPen(QColor("#AAAAAA")))
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Normal))
        painter.drawText(QRectF(bx + 15, by + 130, badge_w - 30, 22), Qt.AlignmentFlag.AlignCenter, "Press [MENU] for Game Switcher   •   Press [B] to Exit")

    def draw_game_switcher(self, painter, theme):
        # 100% Solid dark backdrop to ensure NO background elements bleed through
        painter.fillRect(0, 0, 640, 480, QColor(10, 10, 16, 255))

        gs_top = theme.get_pixmap("gs-top-bar.png") if theme else None
        if gs_top and not gs_top.isNull():
            painter.drawPixmap(0, 0, 640, 45, gs_top)
        # Top Bar
        painter.fillRect(0, 0, 640, 45, QColor(15, 23, 42, 255))
        painter.fillRect(0, 44, 640, 1, QColor("#00f0ff"))

        painter.setPen(QPen(QColor("#00f0ff")))
        painter.setFont(QFont("Segoe UI", 14, QFont.Weight.Black))
        painter.drawText(QRectF(0, 0, 640, 45), Qt.AlignmentFlag.AlignCenter, "⚡ " + tr("view_title_switcher"))

        slots = self.sys_data.switcher_slots
        center_x = 320
        center_y = 230
        card_w = 260
        card_h = 230
        spacing = 290

        for i, slot in enumerate(slots):
            offset = i - self.switcher_idx
            cx = center_x + (offset * spacing) - (card_w // 2)
            cy = center_y - (card_h // 2)

            is_active = (i == self.switcher_idx)

            if -1 <= offset <= 1:
                painter.setPen(QPen(QColor("#00f0ff") if is_active else QColor(255, 255, 255, 40), 2 if is_active else 1))
                painter.setBrush(QColor(30, 41, 59, 240) if is_active else QColor(15, 23, 42, 180))
                painter.drawRoundedRect(cx, cy, card_w, card_h, 14, 14)

                thumb_w = card_w - 20
                thumb_h = 125
                tx = cx + 10
                ty = cy + 10
                
                tgrad = QLinearGradient(tx, ty, tx + thumb_w, ty + thumb_h)
                if i == 0:
                    tgrad.setColorAt(0, QColor("#0284c7"))
                    tgrad.setColorAt(1, QColor("#06b6d4"))
                elif i == 1:
                    tgrad.setColorAt(0, QColor("#8b5cf6"))
                    tgrad.setColorAt(1, QColor("#6366f1"))
                elif i == 2:
                    tgrad.setColorAt(0, QColor("#f43f5e"))
                    tgrad.setColorAt(1, QColor("#fb923c"))
                else:
                    tgrad.setColorAt(0, QColor("#10b981"))
                    tgrad.setColorAt(1, QColor("#14b8a6"))

                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(tgrad))
                painter.drawRoundedRect(tx, ty, thumb_w, thumb_h, 10, 10)

                painter.setPen(QPen(QColor(255, 255, 255, 220)))
                painter.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
                painter.drawText(QRectF(tx, ty, thumb_w, thumb_h), Qt.AlignmentFlag.AlignCenter, "▶")

                painter.setPen(QPen(QColor("#FFFFFF")))
                painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
                disp_title = slot.title if len(slot.title) <= 24 else slot.title[:22] + "..."
                painter.drawText(QRectF(cx + 10, cy + 145, card_w - 20, 22), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, disp_title)

                painter.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
                painter.setPen(QPen(QColor("#00f0ff") if is_active else QColor("#94a3b8")))
                painter.drawText(QRectF(cx + 10, cy + 170, card_w - 20, 20), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, slot.system_name)
                painter.drawText(QRectF(cx + 10, cy + 195, card_w - 20, 20), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, slot.playtime_str)

        painter.fillRect(0, 442, 640, 38, QColor(15, 23, 42, 255))
        painter.fillRect(0, 442, 640, 1, QColor(255, 255, 255, 30))
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        painter.setPen(QPen(QColor("#cbd5e1")))
        painter.drawText(QRectF(0, 442, 640, 38), Qt.AlignmentFlag.AlignCenter, tr("switcher_dock"))

    def draw_stock_main_menu(self, painter):
        # Stock Miyoo Blue Background
        grad = QLinearGradient(0, 0, 0, 480)
        grad.setColorAt(0, QColor("#0a192f"))
        grad.setColorAt(1, QColor("#020c1b"))
        painter.fillRect(0, 0, 640, 480, grad)

        # Stock Banner
        painter.setPen(QPen(QColor("#64ffda")))
        painter.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        painter.drawText(QRectF(0, 60, 640, 35), Qt.AlignmentFlag.AlignCenter, "M I Y O O")

        painter.setPen(QPen(QColor("#8892b0")))
        painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Normal))
        painter.drawText(QRectF(0, 95, 640, 25), Qt.AlignmentFlag.AlignCenter, "Stock NAND Firmware (No OnionOS on MicroSD)")

        # 4 Stock Main Icons
        stock_tabs = [
            ("Games", "Consoles / ROMs", "#007aff"),
            ("RetroArch", "Stock RetroArch Cores", "#ff9500"),
            ("Apps", "Stock System Tools", "#34c759"),
            ("Settings", "Miyoo Factory Settings", "#af52de")
        ]

        grid_x = 70
        grid_y = 145
        col_w = 230
        row_h = 120

        for i, (t_name, t_sub, t_col) in enumerate(stock_tabs):
            r = i // 2
            c = i % 2
            x = grid_x + c * (col_w + 40)
            y = grid_y + r * (row_h + 20)

            is_sel = (i == (self.current_tab % 4))
            
            painter.setPen(QPen(QColor(t_col if is_sel else "#233554"), 2 if is_sel else 1))
            painter.setBrush(QBrush(QColor(20, 30, 50, 240) if is_sel else QColor(10, 20, 35, 200)))
            painter.drawRoundedRect(x, y, col_w, row_h, 12, 12)

            if is_sel:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(t_col)))
                painter.drawRoundedRect(x + 12, y + 12, 40, 40, 8, 8)
                painter.setPen(QPen(QColor("#FFFFFF")))
                painter.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
                painter.drawText(QRectF(x + 12, y + 12, 40, 40), Qt.AlignmentFlag.AlignCenter, "★")
            else:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor("#233554")))
                painter.drawRoundedRect(x + 12, y + 12, 40, 40, 8, 8)
                painter.setPen(QPen(QColor("#8892b0")))
                painter.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
                painter.drawText(QRectF(x + 12, y + 12, 40, 40), Qt.AlignmentFlag.AlignCenter, "•")

            painter.setPen(QPen(QColor("#FFFFFF") if is_sel else QColor("#ccd6f6")))
            painter.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
            painter.drawText(QRectF(x + 60, y + 15, col_w - 70, 25), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, t_name)

            painter.setPen(QPen(QColor("#8892b0")))
            painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Normal))
            painter.drawText(QRectF(x + 15, y + 65, col_w - 30, 40), Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap, t_sub)

    def draw_no_sd_screen(self, painter):
        painter.fillRect(0, 0, 640, 480, QColor("#0d1117"))

        # Red Alert Box
        box_w, box_h = 520, 310
        bx = (640 - box_w) // 2
        by = (480 - box_h) // 2

        painter.setPen(QPen(QColor("#f85149"), 2))
        painter.setBrush(QBrush(QColor("#161b22")))
        painter.drawRoundedRect(bx, by, box_w, box_h, 16, 16)

        painter.setPen(QPen(QColor("#f85149")))
        painter.setFont(QFont("Segoe UI", 34, QFont.Weight.Bold))
        painter.drawText(QRectF(bx, by + 15, box_w, 45), Qt.AlignmentFlag.AlignCenter, "⚠️")

        painter.setPen(QPen(QColor("#ffffff")))
        painter.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        painter.drawText(QRectF(bx + 20, by + 65, box_w - 40, 30), Qt.AlignmentFlag.AlignCenter, "NO MICROSD CARD DETECTED")

        painter.setPen(QPen(QColor("#e6edf3")))
        painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Normal))
        painter.drawText(QRectF(bx + 30, by + 105, box_w - 60, 110), Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, 
            "The device is running in minimal recovery mode because no MicroSD card was found at the selected path.\n\nPlease select an active drive or folder in the right control panel.")

        painter.setPen(QPen(QColor("#58a6ff")))
        painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        painter.drawText(QRectF(bx + 20, by + 240, box_w - 40, 35), Qt.AlignmentFlag.AlignCenter, "⚡ Select SD Drive in Studio Control Deck to Mount")

    def draw_stock_menu_dialog(self, painter):
        painter.fillRect(0, 0, 640, 480, QColor(0, 0, 0, 220))
        
        box_w, box_h = 460, 200
        bx = (640 - box_w) // 2
        by = (480 - box_h) // 2

        painter.setPen(QPen(QColor("#f59e0b"), 2))
        painter.setBrush(QBrush(QColor("#18181b")))
        painter.drawRoundedRect(bx, by, box_w, box_h, 14, 14)

        painter.setPen(QPen(QColor("#f59e0b")))
        painter.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        painter.drawText(QRectF(bx + 20, by + 20, box_w - 40, 30), Qt.AlignmentFlag.AlignCenter, "Miyoo Stock OS (Factory Firmware)")

        painter.setPen(QPen(QColor("#e4e4e7")))
        painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Normal))
        painter.drawText(QRectF(bx + 30, by + 65, box_w - 60, 60), Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
            "Game Switcher is an exclusive feature of OnionOS.\n\nTo enable Game Switcher and 25 Themes, click 'Install OnionOS to SD' in the right sidebar panel.")

        painter.setPen(QPen(QColor("#a1a1aa")))
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Normal))
        painter.drawText(QRectF(bx + 20, by + 145, box_w - 40, 30), Qt.AlignmentFlag.AlignCenter, "Press [B] or [MENU] to close")
