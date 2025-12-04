"""
Main GUI window for the trading bot.
This is a simplified version - full implementation requires PyQt5.
"""

from utils.logger import get_logger

logger = get_logger()


def launch_gui(testnet: bool = True):
    """
    Launch the GUI application.
    
    Args:
        testnet: Whether to use testnet
    """
    try:
        from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
        from PyQt5.QtCore import Qt
        import sys
        
        class MainWindow(QMainWindow):
            """Main trading bot window."""
            
            def __init__(self, testnet: bool):
                super().__init__()
                self.testnet = testnet
                self.init_ui()
            
            def init_ui(self):
                """Initialize UI components."""
                self.setWindowTitle(f"Bybit Trading Bot ({'Testnet' if self.testnet else 'MAINNET'})")
                self.setGeometry(100, 100, 1200, 800)
                
                # Central widget
                central_widget = QWidget()
                self.setCentralWidget(central_widget)
                
                # Layout
                layout = QVBoxLayout()
                
                # Title
                title = QLabel("Bybit Cryptocurrency Futures Trading Bot")
                title.setAlignment(Qt.AlignCenter)
                title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 20px;")
                layout.addWidget(title)
                
                # Status
                status = QLabel("GUI Implementation In Progress")
                status.setAlignment(Qt.AlignCenter)
                status.setStyleSheet("font-size: 16px; padding: 20px;")
                layout.addWidget(status)
                
                # Info
                info_text = """
                <p style='text-align: center;'>
                The GUI is currently a stub implementation.<br>
                For now, please use the command-line interface:<br><br>
                <b>python main.py</b> - Run the bot<br>
                <b>python main.py --backtest</b> - Run backtests<br><br>
                Full GUI implementation coming soon!
                </p>
                """
                info = QLabel(info_text)
                info.setAlignment(Qt.AlignCenter)
                layout.addWidget(info)
                
                central_widget.setLayout(layout)
        
        # Create application
        app = QApplication(sys.argv)
        window = MainWindow(testnet)
        window.show()
        sys.exit(app.exec_())
        
    except ImportError:
        logger.error("PyQt5 not installed. Please install: pip install PyQt5")
        logger.info("Using command-line mode instead")
        return False
