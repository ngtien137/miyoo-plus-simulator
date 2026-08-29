import os
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QLinearGradient, QRadialGradient
from PyQt6.QtCore import Qt, QRectF, QPointF

class HandheldFrame(QWidget):
    """
    Exact 1:1 Physical Replica of Miyoo Mini Plus Hardware:
    - Real Body: 78.5 mm (W) x 108.0 mm (H) -> Exact Ratio: 1 : 1.3758
    - Real Screen: 3.5" IPS 4:3 (71.12 mm W x 53.34 mm H)
    - Base Canvas Resolution: 640 (W) x 880 (H)
    - Screen Area: 552 x 414 px (Strict 4:3) positioned inside glass bezel
    """
    
    SHELL_COLORS = {
        "Retro Grey (Classic)": {
            "body_grad": ("#d2d2d4", "#b8b8bc"),
            "bezel_color": "#18181a",
            "dpad_color": "#2c2c2e",
            "btn_ab": "#8b1e4b",     # Classic DMG Burgundy / Maroon
            "btn_xy": "#8b1e4b",
            "menu_btn": "#3a3a3c",
            "sel_start": "#5c5c60",
            "text_color": "#48484a"
        },
        "Atomic Purple": {
            "body_grad": ("#5c3a70", "#3a1d48"),
            "bezel_color": "#181020",
            "dpad_color": "#22112e",
            "btn_ab": "#a64db8",
            "btn_xy": "#a64db8",
            "menu_btn": "#321640",
            "sel_start": "#4a2860",
            "text_color": "#d5b4e8"
        },
        "Pure White": {
            "body_grad": ("#f5f5f7", "#e1e1e6"),
            "bezel_color": "#151515",
            "dpad_color": "#d0d0d5",
            "btn_ab": "#3a3a3c",
            "btn_xy": "#3a3a3c",
            "menu_btn": "#c0c0c5",
            "sel_start": "#c0c0c5",
            "text_color": "#707075"
        },
        "Solid Black": {
            "body_grad": ("#2c2c2e", "#1c1c1e"),
            "bezel_color": "#0d0d0e",
            "dpad_color": "#151516",
            "btn_ab": "#3a3a3c",
            "btn_xy": "#3a3a3c",
            "menu_btn": "#252528",
            "sel_start": "#252528",
            "text_color": "#8e8e93"
        }
    }

    # Exact Base Dimensions (Ratio: 880 / 640 = 1.375, matching 108.0 / 78.5)
    BASE_WIDTH = 640
    BASE_HEIGHT = 880

    # Screen Bezel Glass
    BEZEL_X = 28
    BEZEL_Y = 22
    BEZEL_W = 584
    BEZEL_H = 460

    # Screen Active Display (Strict 4:3 Ratio: 552 x 414)
    SCREEN_X = 44
    SCREEN_Y = 36
    SCREEN_W = 552
    SCREEN_H = 414

    def __init__(self, screen_canvas, scale=0.90, parent=None):
        super().__init__(parent)
        self.canvas = screen_canvas
        self.current_shell = "Retro Grey (Classic)"
        self.scale_factor = scale
        
        self.pressed_btn = None
        self.btn_rects = {}
        
        # Mount Canvas as child
        self.canvas.setParent(self)
        self.update_dimensions()
        self.init_button_zones()

    def set_scale_factor(self, scale):
        self.scale_factor = max(0.5, min(1.2, scale))
        self.update_dimensions()
        self.init_button_zones()
        self.update()

    def update_dimensions(self):
        w = int(self.BASE_WIDTH * self.scale_factor)
        h = int(self.BASE_HEIGHT * self.scale_factor)
        self.setFixedSize(w, h)
        if hasattr(self, 'canvas') and self.canvas:
            cw = int(self.SCREEN_W * self.scale_factor)
            ch = int(self.SCREEN_H * self.scale_factor)
            cx = int(self.SCREEN_X * self.scale_factor)
            cy = int(self.SCREEN_Y * self.scale_factor)
            self.canvas.setFixedSize(cw, ch)
            self.canvas.move(cx, cy)
            self.canvas.show()

    def set_shell(self, shell_name):
        if shell_name in self.SHELL_COLORS:
            self.current_shell = shell_name
            self.update()

    def init_button_zones(self):
        s = self.scale_factor
        
        # D-pad center at (155 * s, 600 * s)
        dcx = 155 * s
        dcy = 600 * s
        d_size = 46 * s
        self.btn_rects["UP"] = QRectF(dcx - d_size/2, dcy - d_size*1.4, d_size, d_size)
        self.btn_rects["DOWN"] = QRectF(dcx - d_size/2, dcy + d_size*0.4, d_size, d_size)
        self.btn_rects["LEFT"] = QRectF(dcx - d_size*1.4, dcy - d_size/2, d_size, d_size)
        self.btn_rects["RIGHT"] = QRectF(dcx + d_size*0.4, dcy - d_size/2, d_size, d_size)
        self.btn_rects["DPAD_CENTER"] = QRectF(dcx - d_size/2, dcy - d_size/2, d_size, d_size)

        # Action buttons center at (485 * s, 600 * s)
        acx = 485 * s
        acy = 600 * s
        b_rad = 23 * s
        spacing = 50 * s
        self.btn_rects["X"] = QRectF(acx - b_rad, acy - spacing - b_rad, b_rad*2, b_rad*2)
        self.btn_rects["Y"] = QRectF(acx - spacing - b_rad, acy - b_rad, b_rad*2, b_rad*2)
        self.btn_rects["A"] = QRectF(acx + spacing - b_rad, acy - b_rad, b_rad*2, b_rad*2)
        self.btn_rects["B"] = QRectF(acx - b_rad, acy + spacing - b_rad, b_rad*2, b_rad*2)

        # Center Menu Button at (320 * s, 560 * s)
        self.btn_rects["MENU"] = QRectF(299 * s, 539 * s, 42 * s, 42 * s)

        # Select / Start at (260 * s, 680 * s) and (332 * s, 680 * s)
        self.btn_rects["SELECT"] = QRectF(255 * s, 672 * s, 52 * s, 20 * s)
        self.btn_rects["START"] = QRectF(333 * s, 672 * s, 52 * s, 20 * s)

    def mousePressEvent(self, event):
        pos = event.position()
        for btn_name, rect in self.btn_rects.items():
            if rect.contains(pos):
                self.pressed_btn = btn_name
                self.handle_button_action(btn_name)
                self.update()
                break

    def mouseReleaseEvent(self, event):
        if self.pressed_btn:
            self.pressed_btn = None
            self.update()

    def handle_button_action(self, btn_name):
        if btn_name == "UP":
            self.canvas.nav_up()
        elif btn_name == "DOWN":
            self.canvas.nav_down()
        elif btn_name == "LEFT":
            self.canvas.nav_left()
        elif btn_name == "RIGHT":
            self.canvas.nav_right()
        elif btn_name == "A":
            self.canvas.press_a()
        elif btn_name == "B":
            self.canvas.press_b()
        elif btn_name == "X":
            self.canvas.press_x()
        elif btn_name == "Y":
            self.canvas.press_y()
        elif btn_name == "MENU":
            self.canvas.toggle_menu()
        elif btn_name == "START":
            self.canvas.press_a()
        elif btn_name == "SELECT":
            self.canvas.press_y()

    def paintEvent(self, event):
        painter = QPainter(self)
        self.draw_frame(painter)

    def draw_frame(self, painter):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        s = self.scale_factor
        painter.scale(s, s)
        
        cfg = self.SHELL_COLORS[self.current_shell]
        
        # 1. Main Handheld Body (640 x 880) - Ergonomic Rounded Rect
        grad = QLinearGradient(0, 0, 0, self.BASE_HEIGHT)
        grad.setColorAt(0, QColor(cfg["body_grad"][0]))
        grad.setColorAt(1, QColor(cfg["body_grad"][1]))
        painter.setPen(QPen(QColor(0, 0, 0, 45), 2))
        painter.setBrush(QBrush(grad))
        painter.drawRoundedRect(6, 6, self.BASE_WIDTH - 12, self.BASE_HEIGHT - 12, 34, 34)

        # 2. Screen Glass Bezel (584 x 460)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(cfg["bezel_color"])))
        painter.drawRoundedRect(self.BEZEL_X, self.BEZEL_Y, self.BEZEL_W, self.BEZEL_H, 16, 16)

        # Power LED (Top Left of Glass)
        painter.setBrush(QBrush(QColor("#00ff66")))
        painter.drawEllipse(self.BEZEL_X + 16, self.BEZEL_Y + 12, 8, 8)

        # "M I Y O O" Logo on Bottom of Glass
        painter.setPen(QPen(QColor(255, 255, 255, 140)))
        painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        painter.drawText(QRectF(self.BEZEL_X, self.BEZEL_Y + self.BEZEL_H - 24, self.BEZEL_W, 20), Qt.AlignmentFlag.AlignCenter, "M I Y O O")

        # 3. D-Pad (Left side)
        dcx, dcy = 155, 600
        d_color = QColor(cfg["dpad_color"])
        
        # D-pad disc depression shadow
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 60)))
        painter.drawEllipse(dcx - 70, dcy - 70, 140, 140)

        # Cross Arms
        painter.setBrush(QBrush(d_color))
        painter.drawRoundedRect(dcx - 62, dcy - 21, 124, 42, 6, 6)
        painter.drawRoundedRect(dcx - 21, dcy - 62, 42, 124, 6, 6)
        
        # Center indentation circle
        painter.setBrush(QBrush(QColor(0, 0, 0, 60)))
        painter.drawEllipse(dcx - 13, dcy - 13, 26, 26)

        # Highlight pressed dpad direction
        if self.pressed_btn in ["UP", "DOWN", "LEFT", "RIGHT"]:
            r = self.btn_rects[self.pressed_btn]
            r_base = QRectF(r.x() / s, r.y() / s, r.width() / s, r.height() / s)
            painter.setBrush(QBrush(QColor(255, 255, 255, 60)))
            painter.drawRoundedRect(r_base, 6, 6)

        # 4. Action Buttons (A, B, X, Y)
        acx, acy = 485, 600
        btn_ab_color = QColor(cfg["btn_ab"])
        btn_xy_color = QColor(cfg["btn_xy"])

        # Base disc depression shadow
        painter.setBrush(QBrush(QColor(0, 0, 0, 40)))
        painter.drawEllipse(acx - 85, acy - 85, 170, 170)

        btns = [
            ("X", self.btn_rects["X"], btn_xy_color),
            ("Y", self.btn_rects["Y"], btn_xy_color),
            ("A", self.btn_rects["A"], btn_ab_color),
            ("B", self.btn_rects["B"], btn_ab_color),
        ]

        for b_name, b_rect, b_col in btns:
            is_pressed = (self.pressed_btn == b_name)
            b_base = QRectF(b_rect.x() / s, b_rect.y() / s, b_rect.width() / s, b_rect.height() / s)
            
            painter.setPen(Qt.PenStyle.NoPen)
            # 3D button shadow
            painter.setBrush(QBrush(b_col.darker(140) if is_pressed else b_col.darker(120)))
            painter.drawEllipse(b_base.adjusted(-2, 2, 2, 4))
            
            # Button Face
            painter.setBrush(QBrush(b_col.lighter(110) if is_pressed else b_col))
            painter.drawEllipse(b_base)

            # Button Letter
            painter.setPen(QPen(QColor("#FFFFFF")))
            painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            painter.drawText(b_base, Qt.AlignmentFlag.AlignCenter, b_name)

        # 5. Menu Button (Center)
        menu_rect = self.btn_rects["MENU"]
        menu_base = QRectF(menu_rect.x() / s, menu_rect.y() / s, menu_rect.width() / s, menu_rect.height() / s)
        menu_col = QColor(cfg["menu_btn"])
        is_menu_pressed = (self.pressed_btn == "MENU")
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(menu_col.lighter(120) if is_menu_pressed else menu_col))
        painter.drawEllipse(menu_base)
        
        painter.setPen(QPen(QColor("#FFFFFF")))
        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        painter.drawText(menu_base, Qt.AlignmentFlag.AlignCenter, "MENU")

        # 6. Select & Start (Pills)
        sel_col = QColor(cfg["sel_start"])
        for s_name in ["SELECT", "START"]:
            s_rect = self.btn_rects[s_name]
            s_base = QRectF(s_rect.x() / s, s_rect.y() / s, s_rect.width() / s, s_rect.height() / s)
            is_s_pressed = (self.pressed_btn == s_name)
            
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(sel_col.lighter(120) if is_s_pressed else sel_col))
            painter.drawRoundedRect(s_base, 8, 8)
            
            painter.setPen(QPen(QColor(cfg["text_color"])))
            painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            label_rect = QRectF(s_base.x() - 10, s_base.y() + 24, s_base.width() + 20, 16)
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, s_name)

        # 7. Speaker Grille Slots (Bottom Right)
        spk_x = 405
        spk_y = 770
        painter.setPen(QPen(QColor(0, 0, 0, 55), 3.5))
        for i in range(5):
            painter.drawLine(spk_x + i*16, spk_y + 32, spk_x + i*16 + 20, spk_y)
