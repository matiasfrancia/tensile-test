"""Simple test to isolate GUI button issue."""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel


class SimpleTestWindow(QMainWindow):
    """Minimal test window to verify button clicks work."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Button Click Test")
        self.setGeometry(100, 100, 400, 300)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        # Status label
        self.status = QLabel("Click the button below")
        layout.addWidget(self.status)

        # Test button
        self.test_btn = QPushButton("Click Me!")
        self.test_btn.clicked.connect(self.on_click)
        layout.addWidget(self.test_btn)

        # Counter
        self.click_count = 0

        print("SimpleTestWindow initialized")
        print(f"Button enabled: {self.test_btn.isEnabled()}")

    def on_click(self):
        """Handle button click."""
        self.click_count += 1
        self.status.setText(f"Button clicked {self.click_count} times!")
        print(f"Button clicked! Count: {self.click_count}")


def main():
    print("Starting simple GUI test...")
    print(f"PyQt6 imported successfully")

    app = QApplication(sys.argv)
    window = SimpleTestWindow()
    window.show()

    print("Window shown, entering event loop...")
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
