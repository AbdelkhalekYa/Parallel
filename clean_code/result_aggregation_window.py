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

        # Results Table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels([
            'Window ID', 'File Path', 'Matches', 'Processing Time (s)'
        ])
        main_layout.addWidget(self.results_table)

        # Overall Results Display
        self.overall_results_display = QTextEdit()
        self.overall_results_display.setReadOnly(True)
        main_layout.addWidget(self.overall_results_display)

    def add_search_result(self, result_dict: dict):
        
        # Add search result from a thread
                
        self.all_results.append(result_dict)
        self.completed_searches += 1

        # Check if all searches are complete
        if self.completed_searches == self.total_windows:
            self.show_aggregated_results()

    def show_aggregated_results(self):
        
        # Display aggregated search results
        
        # Clear previous results
        self.results_table.setRowCount(0)

        # Calculate overall processing time
        end_time = time.time()
        overall_processing_time = end_time - self.start_time

        # Populate results table
        for result in self.all_results:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            
            # Window ID
            self.results_table.setItem(row, 0, QTableWidgetItem(str(result['window_id'])))
            
            # File Path
            self.results_table.setItem(row, 1, QTableWidgetItem(result['filepath']))
            
            # Matches
            matches_str = str(result['match_count'])
            self.results_table.setItem(row, 2, QTableWidgetItem(matches_str))
            
            # Processing Time
            time_str = f"{result['processing_time']:.4f}"
            self.results_table.setItem(row, 3, QTableWidgetItem(time_str))

        # Prepare overall results text
        overall_results = [
            f"Total Search Windows: {self.total_windows}",
            f"Overall Processing Time: {overall_processing_time:.4f} seconds",
            "\nIndividual Window Results:"
        ]

        for result in self.all_results:
            overall_results.append(
                f"Window {result['window_id']}: "
                f"{result['match_count']} matches in {result['filepath']} "
                f"(Processing Time: {result['processing_time']:.4f} s)"
            )

        # Display overall results
        self.overall_results_display.setPlainText('\n'.join(overall_results))
