#!/usr/bin/env python3
"""
Miyoo Mini Plus & OnionOS Studio / Simulator
Entry point script for launching the simulator application.
"""

import os
import sys

# Ensure repository root is in sys.path
if getattr(sys, 'frozen', False):
    repo_root = os.path.dirname(sys.executable)
else:
    repo_root = os.path.dirname(os.path.abspath(__file__))

if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from simulator.main import MiyooSimulatorWindow

def main():
    # Set Windows Taskbar AppUserModelID for custom icon display
    try:
        import ctypes
        myappid = 'miyoo.plus.simulator.studio'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("Miyoo Mini Plus Simulator & Studio")
    app.setApplicationDisplayName("Miyoo Mini Plus Simulator & Studio")
    
    icon_path = os.path.join(repo_root, "assets", "icons", "app_icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    window = MiyooSimulatorWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
