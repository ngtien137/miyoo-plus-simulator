import os
import time

class Game:
    def __init__(self, title, filename, system_code, boxart="", playtime_min=0, is_real=False, real_path=""):
        self.title = title
        self.filename = filename
        self.system_code = system_code
        self.boxart = boxart
        self.playtime_min = playtime_min
        self.is_favorite = False
        self.is_real = is_real
        self.real_path = real_path

class Emulator:
    def __init__(self, name, code, icon_id, rom_folder, games=None):
        self.name = name
        self.code = code
        self.icon_id = icon_id
        self.rom_folder = rom_folder
        self.games = games or []

class AppItem:
    def __init__(self, name, icon_id, description, app_id):
        self.name = name
        self.icon_id = icon_id
        self.description = description
        self.app_id = app_id

class GameSwitcherSlot:
    def __init__(self, title, system_name, screenshot_path, playtime_str):
        self.title = title
        self.system_name = system_name
        self.screenshot_path = screenshot_path
        self.playtime_str = playtime_str

class BootDiagnostics:
    def __init__(self, path=""):
        self.path = path
        self.exists = False
        self.has_tmp_update = False
        self.has_miyoo = False
        self.has_roms = False
        self.has_themes = False
        self.rom_count = 0
        self.theme_count = 0
        self.boot_mode = "STOCK_OS"  # 'ONION_OS', 'STOCK_OS', 'NO_SD'
        self.onion_version = "None"
        self.status_message = ""

class SystemData:
    def __init__(self, workspace_root, sd_root=None):
        self.workspace_root = workspace_root
        self.sd_root = sd_root
        self.boot_diag = BootDiagnostics()
        self.emulators = []
        self.apps = []
        self.expert_emulators = []
        self.favorites = []
        self.switcher_slots = []
        
        self.reload_from_path(self.sd_root or self.workspace_root)

    def reload_from_path(self, target_path):
        """Perform real Linux boot check on target drive/directory."""
        self.sd_root = target_path
        self.boot_diag = self.check_boot_target(target_path)
        self.init_data()

    def check_boot_target(self, path):
        diag = BootDiagnostics(path)
        if not path or not os.path.exists(path):
            diag.exists = False
            diag.boot_mode = "NO_SD"
            diag.status_message = "No MicroSD Card mounted. Running minimal Stock recovery."
            return diag

        diag.exists = True
        tmp_update_path = os.path.join(path, ".tmp_update")
        kayzit_path = os.path.join(path, ".kayzit")
        miyoo_path = os.path.join(path, "miyoo")
        minui_path = os.path.join(path, ".minui")
        koriki_path = os.path.join(path, ".koriki")
        allium_path = os.path.join(path, ".allium")
        roms_path = os.path.join(path, "Roms")
        themes_path = os.path.join(path, "Themes")

        diag.has_tmp_update = os.path.exists(tmp_update_path) and os.path.isdir(tmp_update_path)
        diag.has_miyoo = os.path.exists(miyoo_path) and os.path.isdir(miyoo_path)
        diag.has_roms = os.path.exists(roms_path) and os.path.isdir(roms_path)
        diag.has_themes = os.path.exists(themes_path) and os.path.isdir(themes_path)

        if diag.has_themes:
            try:
                diag.theme_count = len([d for d in os.listdir(themes_path) if os.path.isdir(os.path.join(themes_path, d))])
            except Exception:
                diag.theme_count = 0

        # Multi-OS Detection Pipeline for Miyoo Mini Plus
        if os.path.exists(kayzit_path):
            diag.boot_mode = "CUSTOM_OS"
            diag.onion_version = "Kayzit OS v1.0"
            diag.status_message = "⚡ Kayzit OS (Next-Gen 3D Glass) detected on MicroSD! Running 60FPS ecosystem."
        elif diag.has_tmp_update and diag.has_miyoo:
            diag.boot_mode = "CUSTOM_OS"
            diag.onion_version = "v4.3"
            diag.status_message = "⚡ Enhanced Custom OS detected on MicroSD! Running full multi-system ecosystem."
        elif os.path.exists(minui_path) or os.path.exists(os.path.join(path, "MinUI.zip")):
            diag.boot_mode = "MIN_UI"
            diag.status_message = "🔲 MinUI detected on MicroSD! Running minimalist launcher."
        elif os.path.exists(koriki_path) or os.path.exists(os.path.join(path, "batocera.boot")):
            diag.boot_mode = "KORIKI_OS"
            diag.status_message = "🐧 Koriki / Batocera Linux detected on MicroSD!"
        elif os.path.exists(allium_path):
            diag.boot_mode = "ALLIUM_OS"
            diag.status_message = "🌿 Allium OS detected on MicroSD!"
        else:
            diag.boot_mode = "STOCK_OS"
            diag.status_message = "⚙️ Stock OS: Running official Miyoo factory firmware from NAND Flash / MicroSD."

        return diag

    def init_data(self):
        self.emulators.clear()
        self.apps.clear()
        self.expert_emulators.clear()
        self.favorites.clear()
        self.switcher_slots.clear()

        # Base emulator definitions
        emu_defs = [
            ("Game Boy Advance", "GBA", "gba", "GBA"),
            ("PlayStation", "PS", "ps", "PS"),
            ("Super Nintendo", "SFC", "sfc", "SFC"),
            ("Nintendo Ent. System", "FC", "fc", "FC"),
            ("Arcade Classics", "ARCADE", "arcade", "ARCADE"),
            ("Nintendo DS", "NDS", "nds", "NDS"),
            ("Pico-8 Fantasy Console", "PICO", "pico", "PICO"),
            ("Sega Genesis / MD", "MD", "md", "MD"),
            ("Game Boy Color", "GBC", "gbc", "GBC"),
            ("Game Boy (Original)", "GB", "gb", "GB"),
            ("Neo Geo", "NEOGEO", "neogeo", "NEOGEO"),
            ("Ports & PC Games", "PORTS", "ports", "PORTS"),
        ]

        total_roms = 0
        for name, code, icon_id, folder in emu_defs:
            games = self.scan_games_for_emu(folder, code)
            total_roms += len(games)
            self.emulators.append(Emulator(name, code, icon_id, folder, games))

        self.boot_diag.rom_count = total_roms

        # Populate Favorites
        for emu in self.emulators:
            for g in emu.games:
                if g.is_favorite:
                    self.favorites.append(g)

        if not self.favorites and self.emulators:
            for emu in self.emulators[:3]:
                if emu.games:
                    emu.games[0].is_favorite = True
                    self.favorites.append(emu.games[0])

        # Apps (Full multi-app suite)
        if self.boot_diag.boot_mode in ["CUSTOM_OS", "ONION_OS"]:
            self.apps = [
                AppItem("KTransfer", "ktransfer", "Local Web ROMs & File Transfer over Wi-Fi/LAN (Port 9090)", "web"),
                AppItem("Tweaks", "tweaks", "System configuration, hotkeys & LED tweaks", "tweaks"),
                AppItem("Package Manager", "package_manager", "Install/Uninstall emulator cores and standalone apps", "package"),
                AppItem("Activity Tracker", "activity", "Detailed gameplay statistics and total playtime logs", "activity"),
                AppItem("Theme Switcher", "theme_switcher", "Preview and apply 25+ visual themes with custom BGM", "theme"),
                AppItem("File Manager", "file_manager", "Browse, copy, rename, delete files directly on SD", "files"),
                AppItem("RetroArch", "retroarch", "Direct access to advanced RetroArch frontend configuration", "ra"),
                AppItem("Wi-Fi & Network", "wifi", "Connect to wireless networks, Web Server and Samba", "wifi"),
                AppItem("Search Games", "search", "Global search across all installed ROMs and systems", "search"),
                AppItem("User Guide", "guide", "Miyoo Plus shortcuts, manual and tips", "guide")
            ]
            self.expert_emulators = [
                Emulator("Neo Geo Pocket", "NGP", "ngp", "NGP"),
                Emulator("WonderSwan Color", "WSC", "wsc", "WSC"),
                Emulator("Sega Game Gear", "GG", "gg", "GG"),
                Emulator("Atari 2600", "ATARI", "atari", "ATARI")
            ]
            self.switcher_slots = [
                GameSwitcherSlot("Pokemon - Emerald Version", "Game Boy Advance", "", "23h 40m - Slateport City"),
                GameSwitcherSlot("Castlevania: Symphony of the Night", "PlayStation", "", "14h 50m - Marble Gallery"),
                GameSwitcherSlot("Super Mario World", "Super Nintendo", "", "13h 00m - Donut Plains 2"),
                GameSwitcherSlot("Chrono Trigger", "Super Nintendo", "", "11h 00m - 600 A.D. Guardia"),
            ]
        else:
            # Stock OS mode (Simpler stock factory apps, no Game Switcher)
            self.apps = [
                AppItem("File Explorer", "file_manager", "Stock Miyoo file manager", "files"),
                AppItem("Key Testing", "guide", "Test hardware buttons, D-Pad and LEDs", "test"),
                AppItem("RetroArch (Stock)", "retroarch", "Stock RetroArch Core", "ra"),
                AppItem("Factory Reset", "tweaks", "Restore default NAND settings", "reset")
            ]
            self.expert_emulators = []
            self.switcher_slots = []

    def scan_games_for_emu(self, folder, system_code):
        games = []
        if not self.sd_root:
            return games

        # Scan ROMs strictly from selected drive / SD card
        r_dir = os.path.join(self.sd_root, "Roms", folder)
        if not os.path.exists(r_dir) or not os.path.isdir(r_dir):
            return games

        valid_exts = {'.gba', '.gb', '.gbc', '.nes', '.sfc', '.smc', '.md', '.bin', '.chd', '.iso', '.p8', '.p8.png', '.nds', '.zip', '.7z', '.wad'}

        seen_files = set()
        try:
            for f in sorted(os.listdir(r_dir)):
                ext = os.path.splitext(f)[1].lower()
                if ext in valid_exts and f not in seen_files:
                    seen_files.add(f)
                    full_path = os.path.join(r_dir, f)
                    raw_title = os.path.splitext(f)[0]
                    
                    box_path = os.path.join(r_dir, "Imgs", raw_title + ".png")
                    if not os.path.exists(box_path):
                        box_path = os.path.join(r_dir, "Imgs", raw_title + ".jpg")
                    if not os.path.exists(box_path):
                        box_path = ""
                        
                    g = Game(raw_title, f, system_code, boxart=box_path, is_real=True, real_path=full_path)
                    games.append(g)
        except Exception:
            pass

        return games
