import os
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout
from PyQt6.QtGui import QIcon, QFont, QColor
from PyQt6.QtCore import Qt

from simulator.theme_manager import ThemeManager
from simulator.models import SystemData
from simulator.screen_canvas import ScreenCanvas
from simulator.handheld_frame import HandheldFrame
from simulator.control_deck import ControlDeck
from simulator.recent_history import load_recent_sources, add_recent_source
from simulator.i18n import tr, add_listener

class MiyooSimulatorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("app_title"))
        add_listener(lambda: self.setWindowTitle(tr("app_title")))
        
        # Paths
        if getattr(sys, 'frozen', False):
            project_root = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(base_dir)

        # Detect Default Source Payload / Recent History (Sorted MRU, max 10, valid only)
        parent_dir = os.path.dirname(project_root)
        kayzit_payload = os.path.join(parent_dir, "kayzit-os", "payload")
        local_payload = os.path.join(project_root, "payload")
        fallback_candidates = [kayzit_payload, local_payload, project_root]

        recent_sources = load_recent_sources(project_root, fallback_candidates)
        source_root = recent_sources[0] if recent_sources else project_root

        target_root = "E:\\" if os.path.exists("E:\\") else project_root
        
        # Themes resolution (Source payload with project fallback)
        themes_dir = os.path.join(source_root, "Themes")
        if not os.path.exists(themes_dir) or not os.listdir(themes_dir):
            proj_th = os.path.join(project_root, "Themes")
            if os.path.exists(proj_th) and os.listdir(proj_th):
                themes_dir = proj_th

        # Default Icons resolution (Directly from assets package)
        default_icons_dir = os.path.join(project_root, "assets", "default_icons")
        if not os.path.exists(default_icons_dir):
            default_icons_dir = os.path.join(project_root, "assets", "icons", "default")

        # Window Icon
        icon_path = os.path.join(project_root, "assets", "icons", "app_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Core Engines
        self.theme_mgr = ThemeManager(themes_dir, default_icons_dir)
        self.sys_data = SystemData(project_root, sd_root=source_root)

        # Central Layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)

        # Left: Handheld Frame + Screen Canvas (Exact 1:1.3758 Miyoo hardware ratio)
        self.canvas = ScreenCanvas(self.theme_mgr, self.sys_data)
        self.frame_widget = HandheldFrame(self.canvas, scale=0.90)
        layout.addWidget(self.frame_widget, 0)

        # Right: Control Deck Sidebar (Flexible stretch)
        self.control_deck = ControlDeck(self.theme_mgr, self.canvas, self.frame_widget)
        layout.addWidget(self.control_deck, 1)

        # Modern Dark Window Theme
        self.setStyleSheet("""
            QMainWindow { background-color: #121214; }
            QLabel { color: #f2f2f7; }
            QPushButton { background-color: #2c2c2e; color: #ffffff; border: 1px solid #3a3a3c; border-radius: 6px; padding: 6px 12px; font-size: 12px; }
            QPushButton:hover { background-color: #3a3a3c; }
            QPushButton:pressed { background-color: #007aff; }
            QComboBox { background-color: #2c2c2e; color: #ffffff; border: 1px solid #3a3a3c; border-radius: 6px; padding: 5px; }
            QCheckBox { color: #ffffff; }
            QSlider::groove:horizontal { height: 6px; background: #3a3a3c; border-radius: 3px; }
            QSlider::sub-page:horizontal { background: #007aff; border-radius: 3px; }
            QSlider::handle:horizontal { background: #ffffff; width: 14px; margin-top: -4px; margin-bottom: -4px; border-radius: 7px; }
        """)

        # Set Window Dimensions (Resizable with responsive layout)
        self.setMinimumSize(1120, 830)
        self.resize(1220, 840)

    def keyPressEvent(self, event):
        key = event.key()
        
        # Navigation
        if key in (Qt.Key.Key_Up, Qt.Key.Key_W):
            self.canvas.nav_up()
        elif key in (Qt.Key.Key_Down, Qt.Key.Key_S):
            self.canvas.nav_down()
        elif key in (Qt.Key.Key_Left, Qt.Key.Key_A):
            self.canvas.nav_left()
        elif key in (Qt.Key.Key_Right, Qt.Key.Key_D):
            self.canvas.nav_right()
            
        # Action Buttons
        elif key in (Qt.Key.Key_J, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.canvas.press_a()
        elif key in (Qt.Key.Key_K, Qt.Key.Key_Escape, Qt.Key.Key_Backspace):
            self.canvas.press_b()
        elif key in (Qt.Key.Key_U, Qt.Key.Key_X):
            self.canvas.press_x()
        elif key in (Qt.Key.Key_I, Qt.Key.Key_Y):
            self.canvas.press_y()
            
        # Menu Button (Onion Game Switcher)
        elif key in (Qt.Key.Key_M, Qt.Key.Key_Space):
            self.canvas.toggle_menu()
            
        # Shoulder Buttons
        elif key == Qt.Key.Key_Q:
            self.canvas.nav_left()
        elif key == Qt.Key.Key_E:
            self.canvas.nav_right()
        else:
            super().keyPressEvent(event)

def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    window = MiyooSimulatorWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
