import time
from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QTextEdit, QTableWidget, 
    QTableWidgetItem, QWidget
)

class ResultAggregationWindow(QMainWindow):
    
    # Window to aggregate and display search results from all threads
    
    def __init__(self, total_windows: int):
        super().__init__()
        self.total_windows = total_windows
        self.completed_searches = 0
        self.all_results = []
        self.start_time = time.time()
        
        self.initUI()

    def initUI(self):
        
        # Initialize the Results Aggregation User Interface
        
        self.setWindowTitle('Search Results Aggregation')
        self.setGeometry(200, 200, 800, 600)

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main Layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)


    def add_search_result(self, result_dict: dict):
        
        # Add search result from a thread
                
        self.all_results.append(result_dict)
        self.completed_searches += 1

        # Check if all searches are complete
        if self.completed_searches == self.total_windows:
            self.show_aggregated_results()

