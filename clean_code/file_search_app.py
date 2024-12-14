import sys
from typing import List, Optional
from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QTextEdit, 
    QFileDialog, QTableWidget, QTableWidgetItem, 
    QWidget, QMessageBox
)

from search_thread import SearchThread
from result_aggregation_window import ResultAggregationWindow

class FileSearchApp(QMainWindow):
    def __init__(self):
        
        # Initialize the File Search Application

        super().__init__()
        
        # Core application state
        self.search_threads: List[SearchThread] = []
        self.file_paths: List[str] = []
        
        # Setup main UI
        self.setup_ui()

    def setup_ui(self):
        
        # Comprehensive UI setup method
        
        # Window configuration
        self.setWindowTitle('Parallel File Search Tool')
        self.setGeometry(100, 100, 1000, 700)

        # Central widget and main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        # Add UI components
        self.add_window_configuration_section(main_layout)
        self.add_keyword_search_section(main_layout)
        self.add_search_windows_placeholder(main_layout)
        self.add_results_table(main_layout)
        self.add_overall_results_display(main_layout)

    def add_window_configuration_section(self, main_layout):
        # Add section for configuring number of search windows

        windows_layout = QHBoxLayout()
        windows_layout.addWidget(QLabel('Number of Search Windows:'))
        
        self.num_windows_input = QLineEdit()
        self.num_windows_input.setPlaceholderText('Enter number of windows')
        windows_layout.addWidget(self.num_windows_input)
        
        create_windows_btn = QPushButton('Create Search Windows')
        create_windows_btn.clicked.connect(self.create_search_windows)
        windows_layout.addWidget(create_windows_btn)
        
        main_layout.addLayout(windows_layout)

    def add_keyword_search_section(self, main_layout):
        
        # Add section for entering search keyword
        
        keyword_layout = QHBoxLayout()
        
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText('Enter search keyword')
        keyword_layout.addWidget(self.keyword_input)

        start_search_btn = QPushButton('Start Parallel Search')
        start_search_btn.clicked.connect(self.start_parallel_search)
        keyword_layout.addWidget(start_search_btn)
        
        main_layout.addLayout(keyword_layout)

    def add_search_windows_placeholder(self, main_layout):
        
        # Create placeholder for dynamic search windows
        
        self.search_windows_layout = QHBoxLayout()
        main_layout.addLayout(self.search_windows_layout)

    def add_results_table(self, main_layout):
        
        # Add table for displaying detailed search results
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels([
            'Window', 'File Path', 'Matches', 'Processing Time (s)'
        ])
        main_layout.addWidget(self.results_table)

    def add_overall_results_display(self, main_layout):
        
        # Add text area for displaying overall search results
        
        self.overall_results = QTextEdit()
        self.overall_results.setReadOnly(True)
        main_layout.addWidget(self.overall_results)

    def create_search_windows(self):
        
        # Dynamically create file selection windows based on user input
        
        # Clear existing windows
        while self.search_windows_layout.count():
            widget = self.search_windows_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()
        
        # Reset file paths
        self.file_paths.clear()

        # Validate number of windows
        try:
            num_windows = int(self.num_windows_input.text())
            if num_windows <= 0:
                raise ValueError("Number of windows must be positive")
        except ValueError:
            QMessageBox.warning(self, 'Invalid Input', 'Please enter a valid positive number of windows')
            return

        # Create file selection windows
        for i in range(num_windows):
            window = self.create_single_search_window(i)
            self.search_windows_layout.addWidget(window)

    def create_single_search_window(self, window_index: int) -> QWidget:
        
        # Create a single search window with file selection
        

        
        file_select_widget = QWidget()
        file_select_layout = QVBoxLayout(file_select_widget)
        
        # Window label
        label = QLabel(f'Window {window_index + 1}')
        file_select_layout.addWidget(label)
        
        # File path input
        file_input = QLineEdit()
        file_input.setPlaceholderText('Select file')
        file_select_layout.addWidget(file_input)
        
        # Browse button
        browse_btn = QPushButton('Browse')
        browse_btn.clicked.connect(lambda _, 
                                   idx=window_index, 
                                   input_field=file_input: 
                                   self.select_file(idx, input_field))
        file_select_layout.addWidget(browse_btn)
        
        return file_select_widget

    def select_file(self, window_id: int, file_input: QLineEdit):
        
        # Open file dialog for selecting a file for a specific window
        

        
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
        
        # Initiate parallel search across multiple files
        
        # Validate search parameters
        if not self.validate_search_parameters():
            return

        # Clear previous results
        self.reset_search_results()

        # Create results aggregation window
        results_aggregator = ResultAggregationWindow(len(self.file_paths))

        # Create and start search threads
        self.initialize_search_threads(results_aggregator)

        # Show results aggregation window
        results_aggregator.show()

    def validate_search_parameters(self) -> bool:
        
        # Validate search keyword and file paths
        
        
        keyword = self.keyword_input.text().strip()
        if not keyword:
            QMessageBox.warning(self, 'Missing Keyword', 'Please enter a search keyword')
            return False

        if not self.file_paths or len(self.file_paths) == 0:
            QMessageBox.warning(self, 'No Files', 'Please select files for all windows')
            return False

        return True

    def reset_search_results(self):
        
        # Reset search results display
        
        self.results_table.setRowCount(0)
        self.overall_results.clear()

    def initialize_search_threads(self, results_aggregator):
        
        # Create and start search threads
        
        
        self.search_threads.clear()
        keyword = self.keyword_input.text().strip()

        for i, filepath in enumerate(self.file_paths):
            if filepath:  # Only create thread for windows with selected files
                thread = SearchThread(i+1, filepath, keyword)
                thread.search_complete.connect(self.process_search_result)
                thread.search_complete.connect(results_aggregator.add_search_result)
                thread.start()
                self.search_threads.append(thread)

    def process_search_result(self, result: dict):
        
        # Process and display individual search thread results
        
        
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        
        # Populate results table
        self.results_table.setItem(row, 0, QTableWidgetItem(str(result['window_id'])))
        self.results_table.setItem(row, 1, QTableWidgetItem(result['filepath']))
        self.results_table.setItem(row, 2, QTableWidgetItem(str(result['match_count'])))
        self.results_table.setItem(row, 3, QTableWidgetItem(f"{result['processing_time']:.4f}"))

        # Display detailed results
        self.display_detailed_results(result)

    def display_detailed_results(self, result: dict):
        
        # Display detailed search results in overall results text area
        
        
        result_text = [
            f"Window {result['window_id']} Results:",
            f"File: {result['filepath']}",
            f"Matches: {result['match_count']}",
            f"Processing Time: {result['processing_time']:.4f} seconds"
        ]

        # Add matching lines if available
        if result['results']:
            result_text.append("\nMatching Lines:")
            result_text.extend(result['results'])

        result_text.append("-" * 50 + "\n")

        # Update overall results display
        current_text = self.overall_results.toPlainText()
        self.overall_results.setPlainText(current_text + "\n".join(result_text))
