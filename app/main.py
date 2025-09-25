import os
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Robust import that works for: package run, script run, PyInstaller frozen
try:
    # When running as a package: python -m app.main
    from .gui import MainWindow  # type: ignore
except Exception:
    try:
        # When running as a script or frozen with "app" package preserved
        from app.gui import MainWindow  # type: ignore
    except Exception:
        # Final fallback: import from current directory (PyInstaller/script)
        sys.path.append(os.path.abspath(os.path.dirname(__file__)))
        from gui import MainWindow  # type: ignore


def main():
    # Improve rendering on HiDPI displays
    try:
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    except Exception:
        pass
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
