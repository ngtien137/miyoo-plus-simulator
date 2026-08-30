import os
import sys
import json
import time
import socket
import shutil
import zipfile
import tempfile
import threading
import urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

DEFAULT_PORT = 9090

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

CONSOLE_EXT_MAP = {
    '.gba': 'GBA',
    '.gb': 'GB',
    '.gbc': 'GBC',
    '.nes': 'FC',
    '.sfc': 'SFC',
    '.smc': 'SFC',
    '.md': 'MD',
    '.gen': 'MD',
    '.smd': 'MD',
    '.bin': 'PS',
    '.iso': 'PS',
    '.chd': 'PS',
    '.pbp': 'PS',
    '.cue': 'PS',
    '.nds': 'NDS',
    '.p8': 'PICO',
    '.p8.png': 'PICO',
    '.ngp': 'NGP',
    '.ngc': 'NGP',
    '.ws': 'WSC',
    '.wsc': 'WSC',
    '.gg': 'GG',
    '.a26': 'ATARI'
}

CONSOLE_NAME_MAP = {
    'GBA': 'Game Boy Advance',
    'PS': 'PlayStation',
    'SFC': 'Super Nintendo (SNES)',
    'FC': 'Nintendo Ent. System (NES)',
    'ARCADE': 'Arcade Classics',
    'NEOGEO': 'SNK Neo Geo',
    'MD': 'Sega Genesis / Mega Drive',
    'GBC': 'Game Boy Color',
    'GB': 'Game Boy',
    'NDS': 'Nintendo DS',
    'PICO': 'Pico-8',
    'PORTS': 'PC Ports',
    'NGP': 'Neo Geo Pocket',
    'WSC': 'WonderSwan Color',
    'GG': 'Sega Game Gear',
    'ATARI': 'Atari 2600'
}

class SmartArchiveInspector:
    """
    Deep inspection and intelligent routing engine for ROMs and Archives.
    Handles:
    1. Arcade/MAME/NeoGeo ROMs (keep zip intact -> Roms/ARCADE/ or Roms/NEOGEO/)
    2. Single Console Game inside ZIP -> Extract directly to Roms/<Hệ máy>/
    3. PS1 Multi-track CD (.cue + .bin) inside ZIP -> Extract to Roms/PS/<GameName>/
    4. Multi-ROM Packs inside ZIP -> Extract and distribute to appropriate Roms/<Console>/
    5. Nested Multi-system Packs -> Distribute to matching Roms/<Console>/
    6. Themes Package -> Extract to Themes/<ThemeName>/
    7. BIOS Package -> Extract to BIOS/
    8. Direct ROMs/Saves/BIOS files -> Route immediately
    """

    @staticmethod
    def is_arcade_zip(zip_ref):
        names = zip_ref.namelist()
        if not names:
            return False
        for n in names:
            ext = os.path.splitext(n)[1].lower()
            if ext in ['.gba', '.sfc', '.smc', '.nes', '.cue', '.iso', '.chd', '.pbp', '.nds']:
                return False
            if 'config.json' in n or 'skin/' in n:
                return False

        chip_exts = {'.rom', '.p1', '.c1', '.v1', '.m1', '.s1', '.bin', '.dat', ''}
        chip_count = sum(1 for n in names if os.path.splitext(n)[1].lower() in chip_exts and not n.endswith('/'))
        return chip_count >= 1

    @staticmethod
    def inspect_and_deploy_file(file_bytes, filename, target_root, reporter_cb=None):
        ext = os.path.splitext(filename)[1].lower()
        base_name = os.path.splitext(filename)[0]

        def log_msg(msg):
            if reporter_cb:
                reporter_cb(msg)

        # 1. BIOS detection
        lower_name = filename.lower()
        if 'bios' in lower_name or lower_name in ['scph1001.bin', 'scph5500.bin', 'scph5502.bin', 'scph7001.bin', 'gba_bios.bin', 'bios7.bin', 'bios9.bin']:
            dest_dir = os.path.join(target_root, 'BIOS')
            os.makedirs(dest_dir, exist_ok=True)
            out_file = os.path.join(dest_dir, filename)
            with open(out_file, 'wb') as f:
                f.write(file_bytes)
            log_msg(f'Saved BIOS: {filename} -> BIOS/')
            return {'status': 'success', 'type': 'BIOS', 'dest': f'BIOS/{filename}', 'action': 'saved_bios', 'file': filename}

        # 2. Save file detection (.sav, .state*)
        if ext in ['.sav', '.srm'] or '.state' in ext:
            dest_dir = os.path.join(target_root, 'Saves')
            os.makedirs(dest_dir, exist_ok=True)
            out_file = os.path.join(dest_dir, filename)
            with open(out_file, 'wb') as f:
                f.write(file_bytes)
            log_msg(f'Saved Game Save: {filename} -> Saves/')
            return {'status': 'success', 'type': 'Saves', 'dest': f'Saves/{filename}', 'action': 'saved_save', 'file': filename}

        # 3. Direct ROM file (non-archive)
        if ext in CONSOLE_EXT_MAP:
            console_code = CONSOLE_EXT_MAP[ext]
            dest_dir = os.path.join(target_root, 'Roms', console_code)
            os.makedirs(dest_dir, exist_ok=True)
            out_file = os.path.join(dest_dir, filename)
            with open(out_file, 'wb') as f:
                f.write(file_bytes)
            log_msg(f'Saved ROM: {filename} -> Roms/{console_code}/')
            return {'status': 'success', 'type': console_code, 'dest': f'Roms/{console_code}/{filename}', 'action': 'saved_rom', 'file': filename}

        # 4. ZIP Archive Inspection & Smart Unpacking
        if ext == '.zip':
            temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
            try:
                temp_zip.write(file_bytes)
                temp_zip.close()

                with zipfile.ZipFile(temp_zip.name, 'r') as zf:
                    namelist = zf.namelist()

                    # Case A: Theme Package (contains config.json & skin/)
                    if any('config.json' in n for n in namelist) and any('skin' in n for n in namelist):
                        theme_dir = os.path.join(target_root, 'Themes', base_name)
                        os.makedirs(theme_dir, exist_ok=True)
                        zf.extractall(theme_dir)
                        log_msg(f'Extracted Theme: {base_name} -> Themes/{base_name}/')
                        return {'status': 'success', 'type': 'Theme', 'dest': f'Themes/{base_name}/', 'action': 'extracted_theme', 'file': filename}

                    # Case B: BIOS Package
                    if 'bios' in lower_name or all(os.path.splitext(n)[1].lower() in ['.bin', '.rom'] and 'bios' in n.lower() for n in namelist if not n.endswith('/')):
                        dest_dir = os.path.join(target_root, 'BIOS')
                        os.makedirs(dest_dir, exist_ok=True)
                        zf.extractall(dest_dir)
                        log_msg(f'Extracted BIOS Pack: {filename} -> BIOS/')
                        return {'status': 'success', 'type': 'BIOS', 'dest': 'BIOS/', 'action': 'extracted_bios', 'file': filename}

                    # Case C: Arcade / MAME / NeoGeo
                    if SmartArchiveInspector.is_arcade_zip(zf):
                        c_code = 'NEOGEO' if any(k in lower_name for k in ['neogeo', 'kof', 'mslug', 'samsho', 'fatfur']) else 'ARCADE'
                        dest_dir = os.path.join(target_root, 'Roms', c_code)
                        os.makedirs(dest_dir, exist_ok=True)
                        out_file = os.path.join(dest_dir, filename)
                        shutil.copy2(temp_zip.name, out_file)
                        log_msg(f'Saved Arcade Archive: {filename} -> Roms/{c_code}/')
                        return {'status': 'success', 'type': c_code, 'dest': f'Roms/{c_code}/{filename}', 'action': 'saved_arcade_zip', 'file': filename}

                    # Case D: PS1 Multi-track CD (.cue + .bin)
                    has_cue = any(n.lower().endswith('.cue') for n in namelist)
                    bin_count = sum(1 for n in namelist if n.lower().endswith('.bin'))
                    if has_cue or (bin_count >= 1 and any('track' in n.lower() for n in namelist)):
                        dest_dir = os.path.join(target_root, 'Roms', 'PS', base_name)
                        os.makedirs(dest_dir, exist_ok=True)
                        zf.extractall(dest_dir)
                        log_msg(f'Extracted PS1 CD: {base_name} -> Roms/PS/{base_name}/')
                        return {'status': 'success', 'type': 'PS', 'dest': f'Roms/PS/{base_name}/', 'action': 'extracted_ps_disc', 'file': filename}

                    # Case E: Multi-ROM / Nested Folders Pack
                    extracted_count = 0
                    for member in zf.infolist():
                        if member.is_dir():
                            continue
                        m_name = member.filename
                        m_ext = os.path.splitext(m_name)[1].lower()
                        
                        target_console = None
                        parts = m_name.replace('\\', '/').split('/')
                        for p in parts[:-1]:
                            p_up = p.upper()
                            if p_up in CONSOLE_EXT_MAP.values():
                                target_console = p_up
                                break
                            if p_up in ['SNES', 'SUPER_NINTENDO', 'SFC']:
                                target_console = 'SFC'
                                break
                            if p_up in ['NES', 'FAMICOM', 'FC']:
                                target_console = 'FC'
                                break
                            if p_up in ['MEGADRIVE', 'GENESIS', 'SEGA']:
                                target_console = 'MD'
                                break

                        if not target_console and m_ext in CONSOLE_EXT_MAP:
                            target_console = CONSOLE_EXT_MAP[m_ext]

                        if target_console:
                            c_dir = os.path.join(target_root, 'Roms', target_console)
                            os.makedirs(c_dir, exist_ok=True)
                            base_fname = os.path.basename(m_name)
                            out_path = os.path.join(c_dir, base_fname)
                            with zf.open(member) as src_f, open(out_path, 'wb') as dst_f:
                                shutil.copyfileobj(src_f, dst_f)
                            extracted_count += 1

                    if extracted_count > 0:
                        log_msg(f'Extracted {extracted_count} ROMs from {filename} -> Roms/')
                        return {'status': 'success', 'type': 'Pack', 'dest': f'Roms/ ({extracted_count} games)', 'action': 'extracted_pack', 'count': extracted_count, 'file': filename}

                    # If no known ROM extension found inside, save intact to Roms/ARCADE/
                    dest_dir = os.path.join(target_root, 'Roms', 'ARCADE')
                    os.makedirs(dest_dir, exist_ok=True)
                    out_file = os.path.join(dest_dir, filename)
                    shutil.copy2(temp_zip.name, out_file)
                    log_msg(f'Saved Archive: {filename} -> Roms/ARCADE/')
                    return {'status': 'success', 'type': 'ARCADE', 'dest': f'Roms/ARCADE/{filename}', 'action': 'saved_zip', 'file': filename}
            finally:
                if os.path.exists(temp_zip.name):
                    try:
                        os.unlink(temp_zip.name)
                    except Exception:
                        pass

        # 5. Fallback for other file types
        dest_dir = os.path.join(target_root, 'Media')
        os.makedirs(dest_dir, exist_ok=True)
        out_file = os.path.join(dest_dir, filename)
        with open(out_file, 'wb') as f:
            f.write(file_bytes)
        log_msg(f'Saved File: {filename} -> Media/')
        return {'status': 'success', 'type': 'Media', 'dest': f'Media/{filename}', 'action': 'saved_media', 'file': filename}


class KTransferServerManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = KTransferServerManager()
        return cls._instance

    def __init__(self):
        self.server = None
        self.server_thread = None
        self.is_running = False
        self.port = DEFAULT_PORT
        self.target_dir = ''
        self.local_ip = get_local_ip()
        self.current_activity = 'Idle (Ready to receive files)'
        self.transferred_count = 0
        self.recent_logs = []
        self.status_listeners = []
        self.lock = threading.Lock()

    def add_listener(self, cb):
        if cb not in self.status_listeners:
            self.status_listeners.append(cb)

    def remove_listener(self, cb):
        if cb in self.status_listeners:
            self.status_listeners.remove(cb)

    def set_activity(self, msg, count_inc=0):
        with self.lock:
            self.current_activity = msg
            if count_inc > 0:
                self.transferred_count += count_inc
            ts = time.strftime('%H:%M:%S')
            self.recent_logs.insert(0, f'[{ts}] {msg}')
            if len(self.recent_logs) > 30:
                self.recent_logs = self.recent_logs[:30]

        for cb in list(self.status_listeners):
            try:
                cb(self.get_status_dict())
            except Exception:
                pass

    def get_status_dict(self):
        with self.lock:
            free_bytes = 0
            total_bytes = 0
            if self.target_dir and os.path.exists(self.target_dir):
                try:
                    usage = shutil.disk_usage(self.target_dir)
                    free_bytes = usage.free
                    total_bytes = usage.total
                except Exception:
                    pass

            return {
                'is_running': self.is_running,
                'ip': self.local_ip,
                'port': self.port,
                'url': f'http://{self.local_ip}:{self.port}',
                'local_url': f'http://localhost:{self.port}',
                'target_dir': self.target_dir,
                'current_activity': self.current_activity,
                'transferred_count': self.transferred_count,
                'free_gb': round(free_bytes / (1024**3), 2),
                'total_gb': round(total_bytes / (1024**3), 2),
                'recent_logs': list(self.recent_logs)
            }

    def start(self, target_dir, port=DEFAULT_PORT):
        if self.is_running:
            self.stop()

        self.target_dir = os.path.abspath(target_dir)
        self.port = port
        self.local_ip = get_local_ip()

        handler_cls = make_ktransfer_handler(self)
        try:
            self.server = ThreadingHTTPServer(('0.0.0.0', self.port), handler_cls)
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            self.is_running = True
            self.set_activity(f'Server started on http://{self.local_ip}:{self.port}')
            return True, f'http://{self.local_ip}:{self.port}'
        except Exception as e:
            self.is_running = False
            return False, str(e)

    def stop(self):
        if self.server:
            try:
                self.server.shutdown()
                self.server.server_close()
            except Exception:
                pass
            self.server = None
        self.is_running = False
        self.set_activity('Server stopped')


def get_dir_tree(root_dir, max_depth=3, cur_depth=0):
    if not os.path.exists(root_dir) or not os.path.isdir(root_dir):
        return []
    items = []
    try:
        for entry in sorted(os.listdir(root_dir)):
            full_p = os.path.join(root_dir, entry)
            if os.path.isdir(full_p):
                child_nodes = []
                if cur_depth < max_depth:
                    child_nodes = get_dir_tree(full_p, max_depth, cur_depth + 1)
                items.append({
                    'name': entry,
                    'path': entry,
                    'type': 'dir',
                    'children': child_nodes
                })
    except Exception:
        pass
    return items


def make_ktransfer_handler(manager):
    class KTransferHTTPHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def send_json(self, data, code=200):
            body = json.dumps(data, ensure_ascii=False).encode('utf-8')
            self.send_response(code)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self):
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()

        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            q = urllib.parse.parse_qs(parsed.query)

            if parsed.path == '/api/status':
                self.send_json(manager.get_status_dict())
                return

            if parsed.path == '/api/tree':
                tree = get_dir_tree(manager.target_dir)
                self.send_json({'status': 'success', 'tree': tree, 'root': manager.target_dir})
                return

            if parsed.path == '/api/files':
                sub_dir = q.get('dir', [''])[0].strip('/\\')
                target_folder = os.path.join(manager.target_dir, sub_dir)
                files = []
                if os.path.exists(target_folder) and os.path.isdir(target_folder):
                    for f in sorted(os.listdir(target_folder)):
                        fp = os.path.join(target_folder, f)
                        is_d = os.path.isdir(fp)
                        sz = os.path.getsize(fp) if not is_d else 0
                        files.append({
                            'name': f,
                            'is_dir': is_d,
                            'size_bytes': sz,
                            'size_str': f"{round(sz / (1024*1024), 2)} MB" if sz > 1024*1024 else f"{round(sz/1024, 1)} KB"
                        })
                self.send_json({'status': 'success', 'dir': sub_dir, 'files': files})
                return

            if parsed.path == '/api/download':
                rel_file = q.get('file', [''])[0].strip('/\\')
                full_path = os.path.join(manager.target_dir, rel_file)
                if os.path.exists(full_path) and os.path.isfile(full_path):
                    sz = os.path.getsize(full_path)
                    fname = os.path.basename(full_path)
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/octet-stream')
                    self.send_header('Content-Disposition', f'attachment; filename="{fname}"')
                    self.send_header('Content-Length', str(sz))
                    self.end_headers()
                    with open(full_path, 'rb') as f:
                        shutil.copyfileobj(f, self.wfile)
                    return
                else:
                    self.send_error(404, 'File not found')
                    return

            html = get_ktransfer_html(manager)
            body = html.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            parsed = urllib.parse.urlparse(self.path)

            if parsed.path == '/api/mkdir':
                content_len = int(self.headers.get('Content-Length', 0))
                raw_data = self.rfile.read(content_len).decode('utf-8')
                try:
                    payload = json.loads(raw_data)
                    new_folder = payload.get('path', '').strip('/\\')
                    if new_folder:
                        full_dir = os.path.join(manager.target_dir, new_folder)
                        os.makedirs(full_dir, exist_ok=True)
                        manager.set_activity(f"Created Folder: {new_folder}")
                        self.send_json({'status': 'success', 'created': new_folder})
                        return
                except Exception as e:
                    self.send_json({'status': 'error', 'message': str(e)}, 400)
                    return

            if parsed.path in ['/api/upload', '/api/upload_to_dir']:
                content_type = self.headers.get('Content-Type', '')
                if 'multipart/form-data' not in content_type:
                    self.send_json({'status': 'error', 'message': 'Expected multipart/form-data'}, 400)
                    return

                boundary = content_type.split('boundary=')[-1].encode('ascii')
                content_len = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_len)

                parts = body.split(b'--' + boundary)
                uploaded_results = []
                target_sub_dir = ''

                for part in parts:
                    if b'Content-Disposition:' not in part:
                        continue
                    header_end = part.find(b'\r\n\r\n')
                    if header_end == -1:
                        header_end = part.find(b'\n\n')
                        if header_end == -1:
                            continue
                        sep_len = 2
                    else:
                        sep_len = 4
                    headers_part = part[:header_end].decode('utf-8', errors='ignore')
                    file_data = part[header_end + sep_len:]
                    if file_data.endswith(b'\r\n'):
                        file_data = file_data[:-2]
                    elif file_data.endswith(b'\n'):
                        file_data = file_data[:-1]

                    if 'name="target_dir"' in headers_part:
                        target_sub_dir = file_data.decode('utf-8', errors='ignore').strip('/\\')
                        continue

                    if 'filename="' in headers_part:
                        fn_start = headers_part.find('filename="') + 10
                        fn_end = headers_part.find('"', fn_start)
                        filename = headers_part[fn_start:fn_end]
                        if not filename:
                            continue

                        manager.set_activity(f"📥 Receiving: {filename} ({round(len(file_data)/1024, 1)} KB)...")

                        if parsed.path == '/api/upload_to_dir' and target_sub_dir:
                            dest_dir = os.path.join(manager.target_dir, target_sub_dir)
                            os.makedirs(dest_dir, exist_ok=True)
                            out_p = os.path.join(dest_dir, filename)
                            with open(out_p, 'wb') as f:
                                f.write(file_data)
                            res = {'status': 'success', 'dest': f'{target_sub_dir}/{filename}', 'file': filename, 'action': 'direct_upload'}
                            manager.set_activity(f"Saved: {filename} -> {target_sub_dir}/", count_inc=1)
                        else:
                            res = SmartArchiveInspector.inspect_and_deploy_file(
                                file_data, filename, manager.target_dir,
                                reporter_cb=lambda msg: manager.set_activity(msg, count_inc=1)
                            )
                        uploaded_results.append(res)

                self.send_json({'status': 'success', 'results': uploaded_results})
                return

        def do_DELETE(self):
            parsed = urllib.parse.urlparse(self.path)
            q = urllib.parse.parse_qs(parsed.query)
            if parsed.path == '/api/delete':
                rel_file = q.get('file', [''])[0].strip('/\\')
                full_path = os.path.join(manager.target_dir, rel_file)
                if os.path.exists(full_path):
                    try:
                        if os.path.isdir(full_path):
                            shutil.rmtree(full_path)
                        else:
                            os.remove(full_path)
                        manager.set_activity(f"Deleted: {rel_file}")
                        self.send_json({'status': 'success', 'deleted': rel_file})
                        return
                    except Exception as e:
                        self.send_json({'status': 'error', 'message': str(e)}, 500)
                        return
                else:
                    self.send_json({'status': 'error', 'message': 'File not found'}, 404)
                    return

    return KTransferHTTPHandler


def get_ktransfer_html(manager):
    status = manager.get_status_dict()
    ip = status['ip']
    port = status['port']

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>⚡ KTransfer — Miyoo Mini Plus ROMs & File Manager</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
:root {{
  --bg: #07090e;
  --panel: rgba(15, 23, 42, 0.75);
  --panel-border: rgba(0, 240, 255, 0.25);
  --cyan: #00f0ff;
  --purple: #a855f7;
  --green: #10b981;
  --red: #ef4444;
  --text: #f8fafc;
  --text-dim: #94a3b8;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  background: var(--bg);
  color: var(--text);
  font-family: 'Space Grotesk', -apple-system, sans-serif;
  min-height: 100vh;
  padding: 24px;
  background-image: 
    radial-gradient(circle at 10% 20%, rgba(0, 240, 255, 0.08) 0%, transparent 40%),
    radial-gradient(circle at 90% 80%, rgba(168, 85, 247, 0.08) 0%, transparent 40%),
    linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
  background-size: 100% 100%, 100% 100%, 32px 32px, 32px 32px;
}}
.container {{ max-width: 1080px; margin: 0 auto; }}
.header {{
  display: flex; justify-content: space-between; align-items: center;
  flex-wrap: wrap; gap: 16px; padding: 20px 24px;
  background: var(--panel); backdrop-filter: blur(16px);
  border: 1px solid var(--panel-border); border-radius: 16px;
  margin-bottom: 24px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
}}
.logo {{ display: flex; align-items: center; gap: 12px; }}
.logo-badge {{
  width: 44px; height: 44px;
  background: linear-gradient(135deg, #0284c7, #00f0ff);
  border-radius: 12px; display: flex; align-items: center; justify-content: center;
  font-size: 22px; font-weight: bold; box-shadow: 0 0 20px rgba(0, 240, 255, 0.4);
}}
.logo h1 {{ font-size: 22px; font-weight: 700; letter-spacing: -0.5px; }}
.logo span {{ font-size: 12px; color: var(--cyan); letter-spacing: 1.5px; text-transform: uppercase; font-weight: 600; }}
.ip-pill {{
  display: flex; align-items: center; gap: 10px;
  background: rgba(0, 240, 255, 0.1); border: 1px solid rgba(0, 240, 255, 0.3);
  padding: 8px 16px; border-radius: 30px;
  font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 600;
  cursor: pointer; transition: 0.2s;
}}
.ip-pill:hover {{ background: rgba(0, 240, 255, 0.2); border-color: var(--cyan); }}
.dot {{ width: 8px; height: 8px; border-radius: 50%; background: var(--green); box-shadow: 0 0 8px var(--green); animation: pulse 2s infinite; }}
@keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.4; }} }}

.storage-bar {{
  background: var(--panel); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 14px; padding: 16px 20px; margin-bottom: 24px;
  display: flex; flex-direction: column; gap: 8px;
}}
.storage-info {{ display: flex; justify-content: space-between; font-size: 13px; font-weight: 600; color: var(--text-dim); }}
.progress-track {{
  width: 100%; height: 8px; background: rgba(255,255,255,0.06); border-radius: 4px; overflow: hidden;
}}
.progress-fill {{ height: 100%; width: 35%; background: linear-gradient(90deg, #0284c7, var(--cyan)); border-radius: 4px; transition: width 0.4s ease; }}

.tabs {{
  display: flex; gap: 8px; margin-bottom: 20px;
  border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 12px;
}}
.tab-btn {{
  background: transparent; border: none; color: var(--text-dim);
  font-family: inherit; font-size: 15px; font-weight: 600;
  padding: 10px 20px; border-radius: 10px; cursor: pointer; transition: 0.2s;
}}
.tab-btn.active {{
  background: rgba(0, 240, 255, 0.15); color: var(--cyan);
  box-shadow: inset 0 0 0 1px var(--cyan);
}}

.tab-content {{ display: none; }}
.tab-content.active {{ display: block; }}

.drop-zone {{
  border: 2px dashed rgba(0, 240, 255, 0.35); background: rgba(15, 23, 42, 0.5);
  border-radius: 20px; padding: 48px 24px; text-align: center;
  cursor: pointer; transition: all 0.25s ease; position: relative; overflow: hidden;
}}
.drop-zone:hover, .drop-zone.dragover {{
  border-color: var(--cyan); background: rgba(0, 240, 255, 0.05);
  box-shadow: 0 0 40px rgba(0, 240, 255, 0.15);
}}
.drop-icon {{ font-size: 48px; margin-bottom: 16px; display: inline-block; animation: bounce 2s infinite ease-in-out; }}
@keyframes bounce {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-8px); }} }}
.drop-title {{ font-size: 20px; font-weight: 700; margin-bottom: 8px; }}
.drop-subtitle {{ font-size: 13px; color: var(--text-dim); max-width: 500px; margin: 0 auto 20px auto; line-height: 1.5; }}
.file-btn {{
  background: linear-gradient(135deg, #0284c7, var(--cyan));
  color: #07090e; font-weight: 700; font-size: 14px;
  border: none; padding: 12px 28px; border-radius: 30px;
  cursor: pointer; transition: 0.2s; box-shadow: 0 4px 20px rgba(0, 240, 255, 0.3);
}}
.file-btn:hover {{ transform: scale(1.04); box-shadow: 0 6px 25px rgba(0, 240, 255, 0.5); }}

.log-box {{
  margin-top: 24px; background: #0c1017;
  border: 1px solid rgba(255,255,255,0.08); border-radius: 14px;
  padding: 16px; max-height: 220px; overflow-y: auto;
  font-family: 'JetBrains Mono', monospace; font-size: 12px;
}}
.log-item {{ padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.03); color: #cbd5e1; }}
.log-item.success {{ color: var(--cyan); }}
.log-item.error {{ color: var(--red); }}

.tree-panel {{ display: grid; grid-template-columns: 280px 1fr; gap: 20px; }}
.tree-box {{
  background: var(--panel); border: 1px solid var(--panel-border);
  border-radius: 16px; padding: 16px; max-height: 480px; overflow-y: auto;
}}
.tree-node {{ padding: 6px 10px; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 600; display: flex; align-items: center; gap: 6px; }}
.tree-node:hover {{ background: rgba(255,255,255,0.06); }}
.tree-node.selected {{ background: var(--cyan); color: #07090e; }}
.target-badge {{
  padding: 12px 16px; background: rgba(0, 240, 255, 0.1); border: 1px solid rgba(0,240,255,0.3);
  border-radius: 12px; margin-bottom: 16px; font-weight: 600; font-size: 14px;
}}

.browser-grid {{
  display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 14px; margin-bottom: 20px;
}}
.console-card {{
  background: var(--panel); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 14px; padding: 16px; cursor: pointer; transition: 0.2s; text-align: center;
}}
.console-card:hover, .console-card.active {{
  border-color: var(--cyan); background: rgba(0,240,255,0.08); transform: translateY(-3px);
}}
.console-title {{ font-weight: 700; font-size: 16px; margin-top: 8px; }}
.console-count {{ font-size: 12px; color: var(--text-dim); margin-top: 4px; }}

.file-table {{
  width: 100%; border-collapse: collapse; background: var(--panel);
  border-radius: 14px; overflow: hidden; border: 1px solid rgba(255,255,255,0.08);
}}
.file-table th, .file-table td {{ padding: 12px 16px; text-align: left; font-size: 13px; }}
.file-table th {{ background: rgba(255,255,255,0.04); color: var(--text-dim); font-weight: 600; }}
.file-table tr:not(:last-child) td {{ border-bottom: 1px solid rgba(255,255,255,0.04); }}
.action-btn {{
  background: rgba(255,255,255,0.08); border: none; color: #fff;
  padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 600; transition: 0.15s;
}}
.action-btn:hover {{ background: var(--cyan); color: #07090e; }}
.action-btn.delete:hover {{ background: var(--red); color: #fff; }}

@media (max-width: 768px) {{
  .tree-panel {{ grid-template-columns: 1fr; }}
  body {{ padding: 12px; }}
}}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="logo">
      <div class="logo-badge">⚡</div>
      <div>
        <h1>KTransfer</h1>
        <span>Miyoo Mini Plus • Web ROMs Transfer</span>
      </div>
    </div>
    <div class="ip-pill" onclick="navigator.clipboard.writeText('http://{ip}:{port}'); alert('Copied URL: http://{ip}:{port}');">
      <div class="dot"></div>
      <span>http://{ip}:{port}</span>
      <span style="font-size: 11px; opacity: 0.7;">(Click to Copy)</span>
    </div>
  </div>

  <div class="storage-bar">
    <div class="storage-info">
      <span id="storage-text">MicroSD Storage</span>
      <span id="storage-gb">Loading...</span>
    </div>
    <div class="progress-track">
      <div class="progress-fill" id="storage-fill"></div>
    </div>
  </div>

  <div class="tabs">
    <button class="tab-btn active" onclick="switchTab(0)">🎮 Smart ROMs Transfer</button>
    <button class="tab-btn" onclick="switchTab(1)">📁 Any File & Directory Tree</button>
    <button class="tab-btn" onclick="switchTab(2)">🗂️ ROMs & File Browser</button>
  </div>

  <!-- TAB 1: Smart ROMs Transfer -->
  <div class="tab-content active" id="tab-0">
    <div class="drop-zone" id="smart-drop-zone">
      <div class="drop-icon">🎮</div>
      <div class="drop-title">Drop ROMs, BIOS, Saves, Themes, or ZIP Packs Here</div>
      <div class="drop-subtitle">
        Deep Inspector auto-detects <b>GBA, PS, SNES, NES, MD, Arcade, BIOS, Themes</b>. Single games inside ZIPs will be cleanly extracted; Arcade chip sets are preserved.
      </div>
      <input type="file" id="smart-file-input" multiple style="display:none;">
      <button class="file-btn" onclick="document.getElementById('smart-file-input').click()">Browse Files...</button>
    </div>

    <div class="log-box" id="smart-log-box">
      <div class="log-item" style="color: #64748b;">[Activity Log] KTransfer server listening on port {port}. Ready for drag-and-drop transfers...</div>
    </div>
  </div>

  <!-- TAB 2: Any File Transfer & Directory Tree -->
  <div class="tab-content" id="tab-1">
    <div class="tree-panel">
      <div class="tree-box">
        <div style="font-weight: 700; margin-bottom: 12px; display:flex; justify-content:space-between; align-items:center;">
          <span>Target Folders</span>
          <button class="action-btn" onclick="promptNewFolder()">+ New</button>
        </div>
        <div id="tree-container">Loading folder structure...</div>
      </div>
      <div>
        <div class="target-badge" id="selected-target-lbl">🎯 Destination: / (Root)</div>
        <div class="drop-zone" id="tree-drop-zone" style="padding: 32px 20px;">
          <div class="drop-icon" style="font-size: 36px;">📁</div>
          <div class="drop-title" style="font-size: 17px;">Drop Any File to Selected Folder</div>
          <div class="drop-subtitle">Upload scripts, music, pdf guides, configs, apps or custom assets directly to this folder.</div>
          <input type="file" id="tree-file-input" multiple style="display:none;">
          <button class="file-btn" onclick="document.getElementById('tree-file-input').click()">Select Files...</button>
        </div>
        <div class="log-box" id="tree-log-box" style="margin-top: 16px;">
          <div class="log-item" style="color: #64748b;">[Activity Log] Select a folder on the left, then drop files.</div>
        </div>
      </div>
    </div>
  </div>

  <!-- TAB 3: ROMs & File Browser -->
  <div class="tab-content" id="tab-2">
    <div class="browser-grid" id="console-grid"></div>
    <div style="margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
      <h3 id="current-browser-title" style="font-size: 16px; color: var(--cyan);">Installed ROMs</h3>
      <input type="text" id="rom-search" placeholder="Search games..." oninput="filterFiles()" style="background: var(--panel); border: 1px solid rgba(255,255,255,0.15); color: #fff; padding: 6px 14px; border-radius: 8px; font-family: inherit;">
    </div>
    <table class="file-table">
      <thead>
        <tr><th>File Name</th><th>Size</th><th style="width: 140px; text-align: right;">Action</th></tr>
      </thead>
      <tbody id="file-tbody">
        <tr><td colspan="3" style="text-align: center; color: #64748b;">Select a console above to view installed ROMs</td></tr>
      </tbody>
    </table>
  </div>
</div>

<script>
let selectedTreePath = '';
let currentBrowseDir = 'Roms/GBA';
let currentFileList = [];

const consoles = [
  {{ code: 'GBA', name: 'Game Boy Advance', path: 'Roms/GBA', icon: '🕹️' }},
  {{ code: 'PS', name: 'PlayStation', path: 'Roms/PS', icon: '💿' }},
  {{ code: 'SFC', name: 'Super Nintendo', path: 'Roms/SFC', icon: '🎮' }},
  {{ code: 'FC', name: 'NES / Famicom', path: 'Roms/FC', icon: '👾' }},
  {{ code: 'ARCADE', name: 'Arcade Classics', path: 'Roms/ARCADE', icon: '🎰' }},
  {{ code: 'MD', name: 'Sega Genesis', path: 'Roms/MD', icon: '⚡' }},
  {{ code: 'GBC', name: 'Game Boy Color', path: 'Roms/GBC', icon: '🌈' }},
  {{ code: 'NDS', name: 'Nintendo DS', path: 'Roms/NDS', icon: '📱' }},
  {{ code: 'BIOS', name: 'System BIOS', path: 'BIOS', icon: '💾' }},
  {{ code: 'Saves', name: 'Game Saves', path: 'Saves', icon: '⭐' }},
  {{ code: 'Themes', name: 'Themes', path: 'Themes', icon: '🎨' }}
];

function switchTab(idx) {{
  document.querySelectorAll('.tab-btn').forEach((b, i) => b.classList.toggle('active', i === idx));
  document.querySelectorAll('.tab-content').forEach((c, i) => c.classList.toggle('active', i === idx));
  if (idx === 1) loadTree();
  if (idx === 2) renderConsoles();
}}

async function updateStatus() {{
  try {{
    const res = await fetch('/api/status');
    const data = await res.json();
    const free = data.free_gb;
    const total = data.total_gb;
    const used = (total - free).toFixed(1);
    const pct = total > 0 ? Math.min(100, Math.round((used / total) * 100)) : 0;
    
    document.getElementById('storage-gb').innerText = free + ' GB Free / ' + total + ' GB Total';
    document.getElementById('storage-fill').style.width = pct + '%';
  }} catch(e) {{}}
}}
setInterval(updateStatus, 1500);
updateStatus();

const smartDrop = document.getElementById('smart-drop-zone');
const smartInput = document.getElementById('smart-file-input');
smartDrop.addEventListener('dragover', e => {{ e.preventDefault(); smartDrop.classList.add('dragover'); }});
smartDrop.addEventListener('dragleave', () => smartDrop.classList.remove('dragover'));
smartDrop.addEventListener('drop', e => {{
  e.preventDefault(); smartDrop.classList.remove('dragover');
  if (e.dataTransfer.files.length) uploadFilesSmart(e.dataTransfer.files);
}});
smartInput.addEventListener('change', () => {{
  if (smartInput.files.length) uploadFilesSmart(smartInput.files);
}});

async function uploadFilesSmart(files) {{
  const logBox = document.getElementById('smart-log-box');
  for (const f of files) {{
    const formData = new FormData();
    formData.append('file', f);
    addLog(logBox, '⏳ Uploading & Analyzing: ' + f.name + ' (' + Math.round(f.size/1024) + ' KB)...');
    try {{
      const res = await fetch('/api/upload', {{ method: 'POST', body: formData }});
      const data = await res.json();
      if (data.results) {{
        data.results.forEach(r => {{
          addLog(logBox, '✅ Done: ' + r.file + ' -> Destination: ' + r.dest, 'success');
        }});
      }}
    }} catch(e) {{
      addLog(logBox, '❌ Error uploading ' + f.name + ': ' + e, 'error');
    }}
  }}
  updateStatus();
}}

const treeDrop = document.getElementById('tree-drop-zone');
const treeInput = document.getElementById('tree-file-input');
treeDrop.addEventListener('dragover', e => {{ e.preventDefault(); treeDrop.classList.add('dragover'); }});
treeDrop.addEventListener('dragleave', () => treeDrop.classList.remove('dragover'));
treeDrop.addEventListener('drop', e => {{
  e.preventDefault(); treeDrop.classList.remove('dragover');
  if (e.dataTransfer.files.length) uploadFilesToDir(e.dataTransfer.files);
}});
treeInput.addEventListener('change', () => {{
  if (treeInput.files.length) uploadFilesToDir(treeInput.files);
}});

async function uploadFilesToDir(files) {{
  const logBox = document.getElementById('tree-log-box');
  for (const f of files) {{
    const formData = new FormData();
    formData.append('file', f);
    formData.append('target_dir', selectedTreePath);
    addLog(logBox, '⏳ Uploading to /' + selectedTreePath + ': ' + f.name + '...');
    try {{
      const res = await fetch('/api/upload_to_dir', {{ method: 'POST', body: formData }});
      const data = await res.json();
      addLog(logBox, '✅ Uploaded to /' + selectedTreePath + '/' + f.name, 'success');
    }} catch(e) {{
      addLog(logBox, '❌ Upload Error: ' + e, 'error');
    }}
  }}
  updateStatus();
}}

async function loadTree() {{
  const c = document.getElementById('tree-container');
  try {{
    const res = await fetch('/api/tree');
    const data = await res.json();
    c.innerHTML = renderTreeNodes(data.tree, '');
  }} catch(e) {{ c.innerText = 'Error loading tree'; }}
}}

function renderTreeNodes(nodes, prefix) {{
  let html = '<div class="tree-node ' + (selectedTreePath === '' ? 'selected':'') + '" onclick="selectTreePath(\\'\\')">📁 / (Root)</div>';
  nodes.forEach(n => {{
    const full = prefix ? prefix + '/' + n.name : n.name;
    const sel = selectedTreePath === full ? 'selected' : '';
    html += '<div class="tree-node ' + sel + '" onclick="selectTreePath(\\'' + full + '\\')" style="padding-left: ' + (prefix ? '24px' : '10px') + '">📁 ' + n.name + '</div>';
    if (n.children && n.children.length) {{
      n.children.forEach(c => {{
        const c_full = full + '/' + c.name;
        const c_sel = selectedTreePath === c_full ? 'selected' : '';
        html += '<div class="tree-node ' + c_sel + '" onclick="selectTreePath(\\'' + c_full + '\\')" style="padding-left: 36px">📂 ' + c.name + '</div>';
      }});
    }}
  }});
  return html;
}}

function selectTreePath(p) {{
  selectedTreePath = p;
  document.getElementById('selected-target-lbl').innerText = '🎯 Destination: /' + (p || '(Root)');
  loadTree();
}}

async function promptNewFolder() {{
  const name = prompt('Enter new folder name (relative to /' + selectedTreePath + '):');
  if (name) {{
    const target = selectedTreePath ? selectedTreePath + '/' + name : name;
    await fetch('/api/mkdir', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ path: target }})
    }});
    loadTree();
  }}
}}

function renderConsoles() {{
  const grid = document.getElementById('console-grid');
  grid.innerHTML = consoles.map(c => 
    '<div class="console-card ' + (currentBrowseDir === c.path ? 'active' : '') + '" onclick="browseConsole(\\'' + c.path + '\\', \\'' + c.name + '\\')">' +
      '<div style="font-size: 28px;">' + c.icon + '</div>' +
      '<div class="console-title">' + c.code + '</div>' +
      '<div class="console-count">' + c.name + '</div>' +
    '</div>'
  ).join('');
  browseConsole(currentBrowseDir, 'Game Boy Advance');
}}

async function browseConsole(path, name) {{
  currentBrowseDir = path;
  document.querySelectorAll('.console-card').forEach(card => card.classList.toggle('active', card.innerText.includes(name.split(' ')[0])));
  document.getElementById('current-browser-title').innerText = '📁 ' + name + ' (' + path + ')';
  const tbody = document.getElementById('file-tbody');
  tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; color: #64748b;">Loading files...</td></tr>';
  try {{
    const res = await fetch('/api/files?dir=' + encodeURIComponent(path));
    const data = await res.json();
    currentFileList = data.files;
    renderFileTable(currentFileList);
  }} catch(e) {{
    tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; color: var(--red);">Error loading files</td></tr>';
  }}
}}

function renderFileTable(files) {{
  const tbody = document.getElementById('file-tbody');
  if (!files.length) {{
    tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; color: #64748b;">No ROMs found in this folder. Drop some above!</td></tr>';
    return;
  }}
  tbody.innerHTML = files.map(f => 
    '<tr>' +
      '<td>' + (f.is_dir ? '📁' : '🕹️') + ' ' + f.name + '</td>' +
      '<td style="color: var(--text-dim); font-family: monospace;">' + f.size_str + '</td>' +
      '<td style="text-align: right;">' +
        '<button class="action-btn" onclick="downloadFile(\\'' + currentBrowseDir + '/' + f.name + '\\')">⬇️ Download</button> ' +
        '<button class="action-btn delete" onclick="deleteFile(\\'' + currentBrowseDir + '/' + f.name + '\\')">🗑️</button>' +
      '</td>' +
    '</tr>'
  ).join('');
}}

function filterFiles() {{
  const q = document.getElementById('rom-search').value.toLowerCase();
  const filtered = currentFileList.filter(f => f.name.toLowerCase().includes(q));
  renderFileTable(filtered);
}}

function downloadFile(relPath) {{
  window.open('/api/download?file=' + encodeURIComponent(relPath), '_blank');
}}

async function deleteFile(relPath) {{
  if (confirm('Delete "' + relPath + '"?')) {{
    await fetch('/api/delete?file=' + encodeURIComponent(relPath), {{ method: 'DELETE' }});
    browseConsole(currentBrowseDir, '');
    updateStatus();
  }}
}}

function addLog(container, msg, type) {{
  type = type || '';
  const d = document.createElement('div');
  d.className = 'log-item ' + type;
  d.innerText = '[' + new Date().toLocaleTimeString() + '] ' + msg;
  container.prepend(d);
}}
</script>
</body>
</html>
"""
