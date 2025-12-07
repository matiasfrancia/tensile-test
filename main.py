"""Main entry point for Tensile Testing Platform."""

import sys
import os
from PyQt6.QtWidgets import QApplication
from src.gui.main_window import MainWindow


def main():
    """Run the application."""
    # Get config path
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'specimen.yaml')

    if not os.path.exists(config_path):
        print(f"Error: Config file not found at {config_path}")
        print("Please create config/specimen.yaml with your specimen and calibration settings.")
        sys.exit(1)

    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Tensile Testing Platform")

    # Create and show main window
    window = MainWindow(config_path)
    window.show()

    # Run event loop
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
