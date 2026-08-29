import os
import json
from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtCore import Qt

_audio_initialized = False

def ensure_audio_init():
    global _audio_initialized
    if not _audio_initialized:
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            _audio_initialized = True
        except Exception as e:
            _audio_initialized = False
    return _audio_initialized

class Theme:
    def __init__(self, name, folder_path, config_data):
        self.name = name
        self.folder_path = folder_path
        self.config = config_data
        self.skin_path = os.path.join(folder_path, "skin")
        self.sound_path = os.path.join(folder_path, "sound")
        self.author = config_data.get("author", "Unknown")
        self.description = config_data.get("description", "")
        
        # Pixmap cache
        self._pixmaps = {}
        
        # Parse colors & fonts
        self.title_color = self._parse_color(config_data.get("title", {}).get("color", "#FFFFFF"))
        self.hint_color = self._parse_color(config_data.get("hint", {}).get("color", "#FFFFFF"))
        self.list_color = self._parse_color(config_data.get("list", {}).get("color", "#FFFFFF"))
        self.grid_color = self._parse_color(config_data.get("grid", {}).get("color", "#888888"))
        self.grid_selected_color = self._parse_color(config_data.get("grid", {}).get("selectedcolor", "#FFFFFF"))
        
        bat_cfg = config_data.get("batteryPercentage", {})
        self.bat_visible = bat_cfg.get("visible", True)
        self.bat_color = self._parse_color(bat_cfg.get("color", "#FFFFFF"))
        self.bat_size = bat_cfg.get("size", 16)
        self.bat_offset_x = bat_cfg.get("offsetX", 26)

    def _parse_color(self, hex_str):
        try:
            if hex_str.startswith("#"):
                return QColor(hex_str)
            return QColor("#" + hex_str)
        except Exception:
            return QColor("#FFFFFF")

    def get_skin_image_path(self, filename):
        path = os.path.join(self.skin_path, filename)
        if os.path.exists(path):
            return path
        # Try extra subfolder
        extra_path = os.path.join(self.skin_path, "extra", filename)
        if os.path.exists(extra_path):
            return extra_path
        return None

    def get_pixmap(self, filename):
        if filename in self._pixmaps:
            return self._pixmaps[filename]
        path = self.get_skin_image_path(filename)
        if path and os.path.exists(path):
            pm = QPixmap(path)
            self._pixmaps[filename] = pm
            return pm
        return None

    def get_sound_path(self, sound_name):
        if not os.path.exists(self.sound_path):
            return None
        for ext in [".wav", ".mp3", ".ogg"]:
            p = os.path.join(self.sound_path, sound_name + ext)
            if os.path.exists(p):
                return p
        return None

    def get_preview_path(self):
        p = os.path.join(self.folder_path, "preview.png")
        if os.path.exists(p):
            return p
        return None


class ThemeManager:
    def __init__(self, themes_dir, default_icons_dir):
        self.themes_dir = themes_dir
        self.default_icons_dir = default_icons_dir
        self.themes = {}
        self.current_theme = None
        self.bgm_enabled = True
        self.sfx_enabled = True
        self.bgm_volume = 0.4
        self.sfx_volume = 0.6
        self._sfx_cache = {}
        
        self.scan_themes()
        
        # Set default theme
        if "Silky" in self.themes:
            self.set_theme("Silky")
        elif "Onion Boy" in self.themes:
            self.set_theme("Onion Boy")
        elif self.themes:
            self.set_theme(list(self.themes.keys())[0])

    def scan_themes(self):
        self.themes.clear()
        if not os.path.exists(self.themes_dir):
            return
            
        for root, dirs, files in os.walk(self.themes_dir):
            if "config.json" in files:
                cfg_path = os.path.join(root, "config.json")
                try:
                    with open(cfg_path, "r", encoding="utf-8", errors="ignore") as f:
                        data = json.load(f)
                except Exception:
                    data = {}
                name = data.get("name", os.path.basename(root))
                # Ensure unique name
                original_name = name
                idx = 1
                while name in self.themes:
                    name = f"{original_name} ({idx})"
                    idx += 1
                
                theme = Theme(name, root, data)
                self.themes[name] = theme

    def reload_themes(self, themes_dir=None):
        if themes_dir:
            self.themes_dir = themes_dir
        self.themes.clear()
        self._sfx_cache.clear()
        self.scan_themes()
        if self.themes:
            first = list(self.themes.keys())[0]
            self.set_theme(first)
        else:
            self.current_theme = None

    def set_theme(self, name):
        if name not in self.themes:
            return False
        self.current_theme = self.themes[name]
        self._sfx_cache.clear()
        
        # Handle BGM safely
        if self.bgm_enabled and ensure_audio_init():
            try:
                import pygame
                bgm_path = self.current_theme.get_sound_path("bgm")
                if bgm_path and os.path.exists(bgm_path):
                    pygame.mixer.music.load(bgm_path)
                    pygame.mixer.music.set_volume(self.bgm_volume)
                    pygame.mixer.music.play(-1)
                else:
                    pygame.mixer.music.stop()
            except Exception:
                pass
        return True

    def play_sfx(self, sfx_name):
        if not (self.sfx_enabled and self.current_theme and ensure_audio_init()):
            return
        import pygame
        sound_path = self.current_theme.get_sound_path(sfx_name)
        if not sound_path:
            # Try generic names
            if sfx_name == "change":
                sound_path = self.current_theme.get_sound_path("click") or self.current_theme.get_sound_path("nav")
            elif sfx_name == "select":
                sound_path = self.current_theme.get_sound_path("enter") or self.current_theme.get_sound_path("launch")
            elif sfx_name == "back":
                sound_path = self.current_theme.get_sound_path("exit")
        
        if sound_path:
            try:
                if sound_path not in self._sfx_cache:
                    self._sfx_cache[sound_path] = pygame.mixer.Sound(sound_path)
                snd = self._sfx_cache[sound_path]
                snd.set_volume(self.sfx_volume)
                snd.play()
            except Exception as e:
                print("Error playing SFX:", e)

    def set_bgm_enabled(self, enabled):
        self.bgm_enabled = enabled
        if ensure_audio_init():
            import pygame
            if enabled and self.current_theme:
                bgm_path = self.current_theme.get_sound_path("bgm")
                if bgm_path:
                    try:
                        pygame.mixer.music.load(bgm_path)
                        pygame.mixer.music.set_volume(self.bgm_volume)
                        pygame.mixer.music.play(-1)
                    except Exception:
                        pass
            else:
                try:
                    pygame.mixer.music.stop()
                except Exception:
                    pass

    def set_bgm_volume(self, vol):
        self.bgm_volume = max(0.0, min(1.0, vol))
        if ensure_audio_init():
            try:
                import pygame
                pygame.mixer.music.set_volume(self.bgm_volume)
            except Exception:
                pass

    def set_sfx_enabled(self, enabled):
        self.sfx_enabled = enabled

    def set_sfx_volume(self, vol):
        self.sfx_volume = max(0.0, min(1.0, vol))
        for snd in self._sfx_cache.values():
            try:
                snd.set_volume(self.sfx_volume)
            except Exception:
                pass

    def get_icon_path(self, icon_name, is_app=False):
        # 1. Check theme skin directory first
        if self.current_theme:
            theme_icon = self.current_theme.get_skin_image_path(f"icon-{icon_name}.png")
            if theme_icon:
                return theme_icon
            theme_icon2 = self.current_theme.get_skin_image_path(f"{icon_name}.png")
            if theme_icon2:
                return theme_icon2
        
        # 2. Check default icons
        if is_app:
            p = os.path.join(self.default_icons_dir, "app", f"{icon_name}.png")
            if os.path.exists(p):
                return p
        p = os.path.join(self.default_icons_dir, f"{icon_name}.png")
        if os.path.exists(p):
            return p
        return None
