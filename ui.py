import os
import threading
import time
from typing import List, Optional
from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTextEdit, QFileDialog, 
    QWidget, QDialog, QTableWidget, QTableWidgetItem
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from search_engine import ThreadSafeSearchEngine

class SearchThread(QThread):
    """
    Dedicated thread for searching a single file
    """
    search_complete = pyqtSignal(dict)

    def __init__(self, window_id: int, filepath: str, keyword: str):
        super().__init__()
        self.window_id = window_id
        self.filepath = filepath
        self.keyword = keyword
        self.search_engine = ThreadSafeSearchEngine()

    def run(self):
        """
        Perform search in a background thread
        """
        # Perform search
        results, processing_time = self.search_engine.perform_search(self.filepath, self.keyword)
        
        # Prepare result dictionary
        result_dict = {
            'window_id': self.window_id,
            'filepath': self.filepath,
            'results': results,
            'processing_time': processing_time
        }
        
        # Emit results
        self.search_complete.emit(result_dict)

class ResultAggregationWindow(QMainWindow):
    """
    Window to aggregate and display search results from all threads
    """
    def __init__(self, total_windows: int):
        super().__init__()
        self.total_windows = total_windows
        self.completed_searches = 0
        self.all_results = []
        self.start_time = time.time()
        
        self.initUI()

    def initUI(self):
        """
        Initialize the Results Aggregation User Interface
        """
        self.setWindowTitle('Search Results Aggregation')
        self.setGeometry(200, 200, 800, 600)

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main Layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Aggregate Results Button
        aggregate_btn = QPushButton('Aggregate Results')
        aggregate_btn.clicked.connect(self.show_aggregated_results)
        main_layout.addWidget(aggregate_btn)

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
        """
        Add search result from a thread
        
        :param result_dict: Dictionary containing search results
        """
        self.all_results.append(result_dict)
        self.completed_searches += 1

        # Check if all searches are complete
        if self.completed_searches == self.total_windows:
            self.show_aggregated_results()

    def show_aggregated_results(self):
        """
        Display aggregated search results
        """
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
            matches_str = str(len(result['results']))
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
                f"{len(result['results'])} matches in {result['filepath']} "
                f"(Processing Time: {result['processing_time']:.4f} s)"
            )

        # Display overall results
        self.overall_results_display.setPlainText('\n'.join(overall_results))

class FileSearchApp(QMainWindow):
    def __init__(self, window_id: int = 1, results_aggregator: Optional[ResultAggregationWindow] = None):
        super().__init__()
        self.window_id = window_id
        self.results_aggregator = results_aggregator
        self.search_thread = None
        self.initUI()

    def initUI(self):
        """
        Initialize the User Interface
        """
        self.setWindowTitle(f'File Search Tool - Window {self.window_id}')
        self.setGeometry(100 + (self.window_id * 50), 100 + (self.window_id * 50), 600, 400)

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main Layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Search Controls Layout
        controls_layout = QHBoxLayout()
        
        # File Selection
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText('Select File to Search')
        controls_layout.addWidget(self.file_input)

        # File Browse Button
        browse_btn = QPushButton('Browse')
        browse_btn.clicked.connect(self.select_file)
        controls_layout.addWidget(browse_btn)

        # Keyword Input
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText('Enter Keyword')
        controls_layout.addWidget(self.keyword_input)

        # Search Button
        search_btn = QPushButton('Search')
        search_btn.clicked.connect(self.start_search)
        controls_layout.addWidget(search_btn)

        main_layout.addLayout(controls_layout)

        # Results Display
        self.results_display = QTextEdit()
        self.results_display.setReadOnly(True)
        main_layout.addWidget(self.results_display)

    def select_file(self):
        """
        Open file dialog to select single file
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            'Select File', 
            '', 
            'Text Files (*.txt *.log *.md);;All Files (*)'
        )
        self.file_input.setText(file_path)

    def start_search(self):
        """
        Initiate search in a separate thread
        """
        filepath = self.file_input.text()
        keyword = self.keyword_input.text()

        if not filepath or not keyword:
            self.results_display.setPlainText('Please provide file and keyword')
            return

        # Clear previous results
        self.results_display.clear()

        # Create and start search thread
        self.search_thread = SearchThread(self.window_id, filepath, keyword)
        self.search_thread.search_complete.connect(self.display_results)
        self.search_thread.start()

    def display_results(self, result_dict: dict):
        """
        Display search results in the text area
        
        :param result_dict: Dictionary containing search results
        """
        results = result_dict['results']
        
        if not results:
            self.results_display.setPlainText('No matches found.')
            return

        # Format results
        formatted_results = [
            f"Matches in {result_dict['filepath']}:",
            *results,
            f"\nProcessing Time: {result_dict['processing_time']:.4f} seconds"
        ]

        self.results_display.setPlainText('\n'.join(formatted_results))

        # Add results to aggregation window if available
        if self.results_aggregator:
            self.results_aggregator.add_search_result(result_dict)