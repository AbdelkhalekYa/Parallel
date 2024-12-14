"""
Improved Parallel File Search Tool

This application provides a multi-window file search utility with parallel 
processing and consolidated result reporting.
"""

import os
import sys
import time
import threading
from typing import List, Optional, Tuple
from queue import Queue

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, 
    QWidget, QTableWidget, QTableWidgetItem
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt

class ThreadSafeSearchEngine:
    """
    Thread-safe search engine for efficient file searching
    """
    def __init__(self):
        self.search_results: List[str] = []
        self.results_lock = threading.Lock()
        self.total_processing_time = 0.0

    def search_file(self, filepath: str, keyword: str) -> Tuple[Optional[List[str]], float]:
        """
        Search for keyword in a single file.
        
        :param filepath: Path to the file to search
        :param keyword: Keyword to search for
        :return: Tuple of (matching lines or None, processing time)
        """
        start_time = time.time()
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                matches = [line.strip() for line in file if keyword.lower() in line.lower()]
                end_time = time.time()
                processing_time = end_time - start_time
                return (matches if matches else None, processing_time)
        except (IOError, PermissionError) as e:
            end_time = time.time()
            processing_time = end_time - start_time
            print(f"Error reading file {filepath}: {e}")
            return (None, processing_time)

    def perform_search(self, filepath: str, keyword: str) -> Tuple[List[str], float]:
        """
        Perform search on a single file and store results
        
        :param filepath: Path to the file
        :param keyword: Keyword to search for
        :return: Tuple of (search results, processing time)
        """
        try:
            results, processing_time = self.search_file(filepath, keyword)
            
            # Use lock to safely update results
            with self.results_lock:
                if results:
                    self.search_results.extend(results)
                self.total_processing_time += processing_time
            
            return results or [], processing_time
        except Exception as e:
            print(f"Unexpected error in search: {e}")
            return [], 0.0

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
        results, processing_time = self.search_engine.perform_search(self.filepath, self.keyword)
        
        # Prepare result dictionary
        result_dict = {
            'window_id': self.window_id,
            'filepath': self.filepath,
            'results': results,
            'match_count': len(results),
            'processing_time': processing_time
        }
        
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

class FileSearchApp(QMainWindow):
    def __init__(self, results_aggregator: Optional[ResultAggregationWindow] = None):
        super().__init__()
        self.results_aggregator = results_aggregator
        self.search_threads = []
        self.file_paths = []
        
        self.initUI()

    def initUI(self):
        """
        Initialize the User Interface
        """
        self.setWindowTitle('Parallel File Search Tool')
        self.setGeometry(100, 100, 1000, 700)

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main Layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Number of Search Windows Section
        windows_layout = QHBoxLayout()
        windows_layout.addWidget(QLabel('Number of Search Windows:'))
        
        self.num_windows_input = QLineEdit()
        self.num_windows_input.setPlaceholderText('Enter number of windows')
        windows_layout.addWidget(self.num_windows_input)
        
        create_windows_btn = QPushButton('Create Search Windows')
        create_windows_btn.clicked.connect(self.create_search_windows)
        windows_layout.addWidget(create_windows_btn)
        
        main_layout.addLayout(windows_layout)

        # Keyword Input Section
        keyword_layout = QHBoxLayout()
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText('Enter search keyword')
        keyword_layout.addWidget(self.keyword_input)

        start_search_btn = QPushButton('Start Parallel Search')
        start_search_btn.clicked.connect(self.start_parallel_search)
        keyword_layout.addWidget(start_search_btn)
        
        main_layout.addLayout(keyword_layout)

        # Search Windows Placeholder
        self.search_windows_layout = QHBoxLayout()
        main_layout.addLayout(self.search_windows_layout)

        # Detailed Results Table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels([
            'Window', 'File Path', 'Matches', 'Processing Time (s)'
        ])
        main_layout.addWidget(self.results_table)

        # Overall Results Display
        self.overall_results = QTextEdit()
        self.overall_results.setReadOnly(True)
        main_layout.addWidget(self.overall_results)

    def create_search_windows(self):
        """
        Create multiple file search windows
        """
        # Clear existing windows
        for i in reversed(range(self.search_windows_layout.count())): 
            widget = self.search_windows_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # Reset file paths
        self.file_paths = []

        # Get number of windows
        try:
            num_windows = int(self.num_windows_input.text())
        except ValueError:
            self.overall_results.setPlainText('Please enter a valid number of windows')
            return

        # Create file selection windows
        for i in range(num_windows):
            # File selection layout
            file_select_widget = QWidget()
            file_select_layout = QVBoxLayout()
            
            # Window label
            label = QLabel(f'Window {i+1}')
            file_select_layout.addWidget(label)
            
            # File path input
            file_input = QLineEdit()
            file_input.setPlaceholderText('Select file')
            file_select_layout.addWidget(file_input)
            
            # Browse button
            browse_btn = QPushButton('Browse')
            browse_btn.clicked.connect(lambda checked, idx=i, file_input=file_input: self.select_file(idx, file_input))
            file_select_layout.addWidget(browse_btn)
            
            file_select_widget.setLayout(file_select_layout)
            self.search_windows_layout.addWidget(file_select_widget)

    def select_file(self, window_id, file_input):
        """
        Open file dialog to select file for a specific window
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            f'Select File for Window {window_id + 1}', 
            '', 
            'Text Files (*.txt *.log *.md);;All Files (*)'
        )
        
        # Update file input and store file path
        file_input.setText(file_path)
        
        # Ensure file paths list is large enough
        while len(self.file_paths) <= window_id:
            self.file_paths.append('')
        
        # Store file path
        self.file_paths[window_id] = file_path

    def start_parallel_search(self):
        """
        Start parallel search across multiple windows
        """
        # Get keyword
        keyword = self.keyword_input.text()
        if not keyword:
            self.overall_results.setPlainText('Please enter a search keyword')
            return

        # Validate file paths
        if not self.file_paths or len(self.file_paths) == 0:
            self.overall_results.setPlainText('Please select files for all windows')
            return

        # Clear previous results
        self.results_table.setRowCount(0)
        self.overall_results.clear()

        # Create results aggregation window
        results_aggregator = ResultAggregationWindow(len(self.file_paths))

        # Create search threads
        self.search_threads = []
        for i, filepath in enumerate(self.file_paths):
            if filepath:  # Only create thread for windows with selected files
                thread = SearchThread(i+1, filepath, keyword)
                thread.search_complete.connect(self.process_search_result)
                thread.search_complete.connect(results_aggregator.add_search_result)
                thread.start()
                self.search_threads.append(thread)

        # Show results aggregation window
        results_aggregator.show()

    def process_search_result(self, result):
        """
        Process search results from a thread
        """
        # Add row to results table
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
        overall_result_text = [
            f"Window {result['window_id']} Results:",
            f"File: {result['filepath']}",
            f"Matches: {result['match_count']}",  # Show match count only once
            f"Processing Time: {result['processing_time']:.4f} seconds"
        ]
        
        # Add matches to the text
        if result['results']:
            overall_result_text.append("\nresults:")
            overall_result_text.append("\n".join(result['results']))  # Add the matches here only once

        overall_result_text.append("-" * 50+ "\n") # Separator line

        # Update the overall results display
        current_text = self.overall_results.toPlainText()
        self.overall_results.setPlainText(current_text + "\n".join(overall_result_text))

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