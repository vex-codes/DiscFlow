import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from src.window import VinylWindow

def main():
    # Enable High DPI scaling
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    app = QApplication(sys.argv)
    
    # Create and show the window
    window = VinylWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
