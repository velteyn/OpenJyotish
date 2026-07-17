"""Entry point: python -m jhora [--gui] or jhora [command]"""

import sys


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--gui":
        sys.argv.pop(1)
        _run_gui()
    else:
        from jhora.cli.main import app
        app()


def _run_gui():
    from PyQt6.QtWidgets import QApplication
    from jhora.ui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("OpenJyotish")
    app.setStyle("Fusion")
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
