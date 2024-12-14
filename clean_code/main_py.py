import sys
from PyQt5.QtWidgets import QApplication
from file_search_app import FileSearchApp

def main():
    """
    Main entry point for the Parallel File Search Tool
    """
    app = QApplication(sys.argv)
    window = FileSearchApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
