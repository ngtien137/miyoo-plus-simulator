import os
import json

CONFIG_FILENAME = "recent_sources.json"
MAX_RECENT = 10

def get_history_file_path(base_dir):
    return os.path.join(base_dir, CONFIG_FILENAME)

def load_recent_sources(base_dir, fallback_candidates=None):
    history_file = get_history_file_path(base_dir)
    loaded_paths = []

    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    loaded_paths = data
        except Exception as e:
            loaded_paths = []

    if not loaded_paths and fallback_candidates:
        loaded_paths = list(fallback_candidates)

    valid_paths = []
    seen = set()

    for p in loaded_paths:
        if not p or not isinstance(p, str):
            continue
        norm_p = os.path.abspath(os.path.normpath(p))
        if norm_p not in seen and os.path.exists(norm_p) and os.path.isdir(norm_p):
            seen.add(norm_p)
            valid_paths.append(norm_p)
            if len(valid_paths) >= MAX_RECENT:
                break

    if not valid_paths and fallback_candidates:
        for p in fallback_candidates:
            if p and os.path.exists(p) and os.path.isdir(p):
                norm_p = os.path.abspath(os.path.normpath(p))
                if norm_p not in seen:
                    seen.add(norm_p)
                    valid_paths.append(norm_p)
                    if len(valid_paths) >= MAX_RECENT:
                        break

    save_recent_sources(base_dir, valid_paths)
    return valid_paths

def save_recent_sources(base_dir, paths_list):
    history_file = get_history_file_path(base_dir)
    clean_list = []
    seen = set()

    for p in paths_list:
        if not p or not isinstance(p, str):
            continue
        norm_p = os.path.abspath(os.path.normpath(p))
        if norm_p not in seen and os.path.exists(norm_p) and os.path.isdir(norm_p):
            seen.add(norm_p)
            clean_list.append(norm_p)
            if len(clean_list) >= MAX_RECENT:
                break

    try:
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(clean_list, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f'Error saving recent sources: ge')

def score_folder(p):
    score = 0
    if os.path.exists(os.path.join(p, ".tmp_update")): score += 5
    if os.path.exists(os.path.join(p, ".kayzit")): score += 5
    if os.path.exists(os.path.join(p, "Themes")): score += 4
    if os.path.exists(os.path.join(p, "miyoo")): score += 4
    if os.path.exists(os.path.join(p, "App")): score += 3
    if os.path.exists(os.path.join(p, "Roms")): score += 3
    if os.path.exists(os.path.join(p, "BIOS")): score += 2
    return score

def find_best_os_payload_path(folder_path):
    if not folder_path or not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        return folder_path

    current_score = score_folder(folder_path)
    if current_score >= 10:
        return os.path.abspath(os.path.normpath(folder_path))

    best_path = folder_path
    best_score = current_score

    candidates = [
        os.path.join(folder_path, "kayzit-os", "payload"),
        os.path.join(folder_path, "payload"),
        os.path.join(folder_path, "Onion-v4.2.0"),
        os.path.join(folder_path, "sdcard"),
    ]
    for cand in candidates:
        if os.path.exists(cand) and os.path.isdir(cand):
            sc = score_folder(cand)
            if sc > best_score:
                best_score = sc
                best_path = cand

    if best_score >= 10:
        return os.path.abspath(os.path.normpath(best_path))

    try:
        for root, dirs, files in os.walk(folder_path):
            rel = os.path.relpath(root, folder_path)
            depth = len(rel.split(os.sep)) if rel != "." else 0
            if depth > 2:
                dirs.clear()
                continue
            if ".git" in dirs: dirs.remove(".git")
            if "node_modules" in dirs: dirs.remove("node_modules")
            if ".temp" in dirs: dirs.remove(".temp")
            if "build" in dirs: dirs.remove("build")

            sc = score_folder(root)
            if sc > best_score:
                best_score = sc
                best_path = root
    except Exception:
        pass

    return os.path.abspath(os.path.normpath(best_path))

def add_recent_source(base_dir, new_path):
    if not new_path or not os.path.exists(new_path) or not os.path.isdir(new_path):
        return None
    resolved_path = find_best_os_payload_path(new_path)
    norm_new = os.path.abspath(os.path.normpath(resolved_path))
    current_list = load_recent_sources(base_dir)

    new_list = [norm_new]
    for p in current_list:
        if p != norm_new and os.path.exists(p) and os.path.isdir(p):
            new_list.append(p)
        if len(new_list) >= MAX_RECENT:
            break

    save_recent_sources(base_dir, new_list)
    return norm_new
