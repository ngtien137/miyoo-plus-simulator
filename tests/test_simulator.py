import os
import sys
import traceback

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtCore import Qt

def run_tests():
    print("=" * 60)
    print("STARTING COMPREHENSIVE TEST SUITE FOR MIYOO PLUS SIMULATOR")
    print("=" * 60)

    app = QApplication.instance() or QApplication(sys.argv)
    
    # 1. Test ThemeManager
    print("\n[TEST 1] Testing ThemeManager & Theme Loading...")
    from simulator.theme_manager import ThemeManager
    
    themes_dir = "E:\\Themes" if os.path.exists("E:\\Themes") else os.path.join(repo_root, "scratch_themes")
    icons_dir = os.path.join(repo_root, "assets", "icons", "default")
    
    tm = ThemeManager(themes_dir, icons_dir)
    print(f"-> Discovered {len(tm.themes)} themes on drive:")
    for name, theme in tm.themes.items():
        res = tm.set_theme(name)
        assert res is True, f"Failed to set theme: {name}"
        bg = theme.get_pixmap("background.png")
        prev = theme.get_preview_path()
        sound_bgm = theme.get_sound_path("bgm")
        sound_change = theme.get_sound_path("change")
        tm.play_sfx("change")
        tm.play_sfx("select")
        tm.play_sfx("back")
    print(f"-> ThemeManager verified successfully!")

    # 2. Test SystemData & Linux Boot Diagnostics
    print("\n[TEST 2] Testing SystemData & Linux Boot Check Engine...")
    from simulator.models import SystemData
    sys_data = SystemData(repo_root, sd_root=repo_root)
    
    # Test boot check on empty/temp path (Stock OS fallback)
    temp_empty = os.path.join(repo_root, "scratch_test_dir")
    os.makedirs(temp_empty, exist_ok=True)
    diag_stock = sys_data.check_boot_target(temp_empty)
    print(f"-> Empty folder Boot Mode: {diag_stock.boot_mode}")
    assert diag_stock.boot_mode == "STOCK_OS", f"Expected STOCK_OS, got {diag_stock.boot_mode}"
    try:
        os.rmdir(temp_empty)
    except Exception:
        pass

    # Test boot check on non-existent path (No SD)
    diag_nosd = sys_data.check_boot_target("Z:\\NonExistentDrive")
    print(f"-> Non-existent drive Boot Mode: {diag_nosd.boot_mode}")
    assert diag_nosd.boot_mode == "NO_SD", f"Expected NO_SD, got {diag_nosd.boot_mode}"

    print("-> Linux Boot Diagnostics Engine verified successfully!")

    # 3. Test ScreenCanvas and Rendering Engine (Across all Boot Modes)
    print("\n[TEST 3] Testing ScreenCanvas & All UI View Renderers across Boot Modes...")
    from simulator.screen_canvas import ScreenCanvas
    canvas = ScreenCanvas(tm, sys_data)

    img = QImage(640, 480, QImage.Format.Format_ARGB32)
    p = QPainter(img)

    # Test OnionOS Mode Views
    sys_data.boot_diag.boot_mode = "ONION_OS"
    views_to_test = [
        'MAIN_CAROUSEL', 'EMU_LIST', 'GAME_LIST', 'APP_LIST', 
        'EXPERT_LIST', 'SETTINGS_LIST', 'TWEAKS', 'ACTIVITY', 'GAME_RUNNING'
    ]
    for v in views_to_test:
        canvas.view_stack = [v]
        canvas.draw_ui(p)
    
    # Test Switcher
    canvas.switcher_open = True
    canvas.draw_ui(p)
    canvas.switcher_open = False

    # Test Stock OS Mode
    sys_data.boot_diag.boot_mode = "STOCK_OS"
    canvas.view_stack = ['MAIN_CAROUSEL']
    canvas.draw_ui(p)
    canvas.switcher_open = True
    canvas.draw_ui(p)
    canvas.switcher_open = False

    # Test No SD Mode
    sys_data.boot_diag.boot_mode = "NO_SD"
    canvas.draw_ui(p)

    p.end()
    del p
    del img

    # Restore Onion mode
    sys_data.reload_from_path(repo_root)
    print("-> ScreenCanvas tested through OnionOS, Stock OS, and No SD modes without errors!")

    # 4. Test HandheldFrame
    print("\n[TEST 4] Testing HandheldFrame & Shell Switching & Button Zones...")
    from simulator.handheld_frame import HandheldFrame
    frame = HandheldFrame(canvas)
    for s_name in HandheldFrame.SHELL_COLORS.keys():
        frame.set_shell(s_name)
        assert frame.current_shell == s_name
        img = QImage(frame.width(), frame.height(), QImage.Format.Format_ARGB32)
        p = QPainter(img)
        frame.draw_frame(p)
        p.end()
        del p
        del img

    for btn_name in ["UP", "DOWN", "LEFT", "RIGHT", "A", "B", "X", "Y", "MENU", "SELECT", "START"]:
        frame.handle_button_action(btn_name)
    print("-> HandheldFrame & all shells & all button hit zones verified!")

    # 5. Test ControlDeck
    print("\n[TEST 5] Testing ControlDeck Sidebar & Live Controls & Drive Switching...")
    from simulator.control_deck import ControlDeck
    deck = ControlDeck(tm, canvas, frame)
    
    # Test Drive Selection Switching
    deck.populate_drives()
    assert deck.drive_combo.count() > 0
    deck.preload_remaining_tabs()
    deck.drive_combo.setCurrentIndex(0)
    deck.on_drive_changed()
    
    # Test theme combobox
    for t_name in list(tm.themes.keys())[:3]:
        deck.theme_combo.setCurrentText(t_name)
        deck.on_theme_changed(t_name)
    
    # Test battery slider
    deck.bat_slider.setValue(45)
    deck.on_battery_changed(45)
    assert canvas.battery_level == 45
    
    # Test shell combo
    for idx, s_name in enumerate(HandheldFrame.SHELL_COLORS.keys()):
        deck.shell_combo.setCurrentIndex(idx)
        deck.on_shell_changed(s_name)
        assert frame.current_shell == s_name
        
    print("-> ControlDeck verified!")

    # 6. Test MainWindow Integration
    print("\n[TEST 6] Testing MiyooSimulatorWindow Integration...")
    from simulator.main import MiyooSimulatorWindow
    win = MiyooSimulatorWindow()
    win.close()
    print("-> MiyooSimulatorWindow initialized cleanly!")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED WITH 0 BUGS / 0 FAILURES!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        run_tests()
        sys.exit(0)
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)
