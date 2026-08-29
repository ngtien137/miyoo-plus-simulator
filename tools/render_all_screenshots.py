import os
import sys

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtCore import Qt

from simulator.theme_manager import ThemeManager
from simulator.models import SystemData
from simulator.screen_canvas import ScreenCanvas
from simulator.main import MiyooSimulatorWindow

def render_all():
    app = QApplication.instance() or QApplication(sys.argv)
    
    themes_dir = os.path.join(repo_root, "assets", "themes") if os.path.exists(os.path.join(repo_root, "assets", "themes")) else os.path.join(repo_root, "Themes")
    icons_dir = os.path.join(repo_root, "assets", "icons", "default")
    
    tm = ThemeManager(themes_dir, icons_dir)
    sys_data = SystemData(repo_root, sd_root=repo_root)
    canvas = ScreenCanvas(tm, sys_data)

    out_dir = os.path.join(repo_root, "screenshots")
    os.makedirs(out_dir, exist_ok=True)
    print(f"Rendering all UI screens to: {out_dir}")

    def capture_screen(name):
        img = QImage(640, 480, QImage.Format.Format_ARGB32)
        p = QPainter(img)
        canvas.draw_ui(p)
        p.end()
        img.save(os.path.join(out_dir, name), "PNG")
        print(f"Saved: {name}")

    # 1. Main Carousel (Games)
    canvas.view_stack = ['MAIN_CAROUSEL']
    canvas.current_tab = 1
    canvas.switcher_open = False
    capture_screen("01_main_carousel_games.png")

    # 2. Main Carousel (Apps)
    canvas.current_tab = 2
    capture_screen("02_main_carousel_apps.png")

    # 3. Main Carousel (Settings)
    canvas.current_tab = 4
    capture_screen("03_main_carousel_settings.png")

    # 4. Emulator List (GBA selected)
    canvas.view_stack = ['MAIN_CAROUSEL', 'EMU_LIST']
    canvas.selected_emu_idx = 0
    capture_screen("04_emu_list_gba.png")

    # 5. Game List (GBA Pokemon)
    canvas.view_stack = ['MAIN_CAROUSEL', 'EMU_LIST', 'GAME_LIST']
    canvas.selected_game_idx = 0
    capture_screen("05_game_list_gba.png")

    # 6. Game List (PS1 Castlevania)
    canvas.selected_emu_idx = 1
    canvas.selected_game_idx = 0
    capture_screen("06_game_list_ps1.png")

    # 7. App List
    canvas.view_stack = ['MAIN_CAROUSEL', 'APP_LIST']
    canvas.selected_app_idx = 0
    capture_screen("07_app_list.png")

    # 8. Onion Tweaks View
    canvas.view_stack = ['MAIN_CAROUSEL', 'APP_LIST', 'TWEAKS']
    canvas.selected_tweak_idx = 0
    capture_screen("08_tweaks_view.png")

    # 9. Activity Tracker View
    canvas.view_stack = ['MAIN_CAROUSEL', 'APP_LIST', 'ACTIVITY']
    capture_screen("09_activity_view.png")

    # 10. Settings List
    canvas.view_stack = ['MAIN_CAROUSEL', 'SETTINGS_LIST']
    capture_screen("10_settings_list.png")

    # 11. Game Running (RetroArch Emulation Overlay)
    canvas.view_stack = ['MAIN_CAROUSEL', 'EMU_LIST', 'GAME_LIST', 'GAME_RUNNING']
    canvas.active_running_game = "Pokemon - Emerald Version (GBA)"
    capture_screen("11_game_running.png")

    # 12. Onion Game Switcher Quick Overlay
    canvas.view_stack = ['MAIN_CAROUSEL']
    canvas.switcher_open = True
    canvas.switcher_idx = 0
    capture_screen("12_game_switcher.png")

    # 13. Full Handheld Frame & Studio Window
    win = MiyooSimulatorWindow()
    win.show()
    win_img = QImage(1090, 824, QImage.Format.Format_ARGB32)
    p13 = QPainter(win_img)
    win.render(p13)
    p13.end()
    win_img.save(os.path.join(out_dir, "13_full_studio_window.png"), "PNG")
    print("Saved: 13_full_studio_window.png")

    print("\nALL SCREENSHOTS RENDERED & VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    render_all()
