#!/usr/bin/env python3
"""
Miyoo Mini Plus & OnionOS Studio / Simulator
Build Script for generating a Standalone Windows Portable Distribution (windows/).
Uses --onedir to ensure 100% compatibility with Windows 11 Smart App Control & Antivirus
(avoiding blocked dynamic extraction into Temp/_MEIPASS).
"""

import os
import sys
import shutil
import subprocess

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(repo_root)

print("=" * 65)
print("BUILDING WINDOWS PORTABLE APPLICATION (SMART APP CONTROL SAFE)")
print("=" * 65)

windows_dir = os.path.join(repo_root, "windows")
temp_dist = os.path.join(repo_root, "dist")
temp_build = os.path.join(repo_root, "build")
icon_path = os.path.join(repo_root, "assets", "icons", "app_icon.ico")

# 1. Clean previous build folders
print("\n[STEP 1] Cleaning previous build folders...")
for d in [windows_dir, temp_dist, temp_build]:
    if os.path.exists(d):
        shutil.rmtree(d, ignore_errors=True)

# 2. Run PyInstaller in --onedir Mode
print("\n[STEP 2] Running PyInstaller compilation...")
cmd = [
    sys.executable, "-m", "PyInstaller",
    "run.py",
    "--name=MiyooPlusSimulator",
    "--windowed",
    "--noconsole",
    f"--icon={icon_path}",
    "--onedir",
    "--clean",
    "--optimize=2",
    "--noupx",
    "--hidden-import=PyQt6",
    "--hidden-import=PyQt6.QtCore",
    "--hidden-import=PyQt6.QtGui",
    "--hidden-import=PyQt6.QtWidgets",
    "--hidden-import=pygame",
    "--distpath=dist",
    "--workpath=build"
]

res = subprocess.run(cmd, cwd=repo_root)
if res.returncode != 0:
    print(f"\n[ERROR] PyInstaller build failed with code {res.returncode}")
    sys.exit(1)

# 3. Copy build contents directly into windows/
os.makedirs(windows_dir, exist_ok=True)
built_folder = os.path.join(temp_dist, "MiyooPlusSimulator")
if os.path.exists(built_folder):
    for item in os.listdir(built_folder):
        s = os.path.join(built_folder, item)
        d = os.path.join(windows_dir, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)

# 4. Copy Assets and Documentation into windows/ folder
print("\n[STEP 3] Copying standalone assets package into windows/ folder...")
assets_src = os.path.join(repo_root, "assets")
assets_dst = os.path.join(windows_dir, "assets")
if os.path.exists(assets_src):
    shutil.copytree(assets_src, assets_dst, dirs_exist_ok=True)

# Copy README & LICENSE
for doc in ["README.md", "LICENSE"]:
    doc_path = os.path.join(repo_root, doc)
    if os.path.exists(doc_path):
        shutil.copy2(doc_path, os.path.join(windows_dir, doc))

# 5. Clean up temporary dist, build, and spec files
if os.path.exists(temp_dist):
    shutil.rmtree(temp_dist, ignore_errors=True)
if os.path.exists(temp_build):
    shutil.rmtree(temp_build, ignore_errors=True)

spec_file = os.path.join(repo_root, "MiyooPlusSimulator.spec")
if os.path.exists(spec_file):
    os.remove(spec_file)

print("\n" + "=" * 65)
print("BUILD COMPLETED 100% SUCCESSFULLY!")
print(f"📁 Standalone Windows Folder: {windows_dir}")
print(f"🚀 Executable to run:         {os.path.join(windows_dir, 'MiyooPlusSimulator.exe')}")
print("=" * 65)
