# main.py
import sys
import time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, 
    QWidget, QTableWidget, QTableWidgetItem
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
import threading

class SearchThread(QThread):
    """
    Dedicated thread for searching a single file
    """
    search_complete = pyqtSignal(dict)

    def __init__(self, filepath: str, keyword: str, window_id: int):
        super().__init__()
        self.filepath = filepath
        self.keyword = keyword
        self.window_id = window_id

    def run(self):
        """
        Perform search in a background thread
        """
        start_time = time.time()
        
        try:
            # Read file
            with open(self.filepath, 'r', encoding='utf-8') as file:
                # Count all occurrences of the keyword in the entire file
                matches = []
                match_count = 0
                for line in file:
                    occurrences = line.lower().count(self.keyword.lower())  # Count keyword occurrences in the line
                    if occurrences > 0:
                        match_count += occurrences
                        matches.extend([line.strip()])  # Store each match found in a line
                
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Prepare result
            result = {
                'window_id': self.window_id,
                'filepath': self.filepath,
                'matches': matches,
                'match_count': match_count,  # Total match count
                'processing_time': processing_time
            }
            
            # Emit results
            self.search_complete.emit(result)
        
        except Exception as e:
            # Handle file reading errors
            processing_time = time.time() - start_time
            result = {
                'window_id': self.window_id,
                'filepath': self.filepath,
                'matches': [],
                'error': str(e),
                'processing_time': processing_time
            }
            self.search_complete.emit(result)


class FileSearchApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Store file paths for search windows
        self.file_paths = []
        
        # Initialize UI
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

        # File Selection Section
        file_layout = QHBoxLayout()
        
        # Number of Search Windows
        self.num_windows_label = QLabel('Number of Search Windows:')
        file_layout.addWidget(self.num_windows_label)
        
        self.num_windows_input = QLineEdit()
        self.num_windows_input.setPlaceholderText('Enter number of windows')
        file_layout.addWidget(self.num_windows_input)
        
        # Create Windows Button
        create_windows_btn = QPushButton('Create Search Windows')
        create_windows_btn.clicked.connect(self.create_search_windows)
        file_layout.addWidget(create_windows_btn)

        main_layout.addLayout(file_layout)

        # Keyword Input
        keyword_layout = QHBoxLayout()
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText('Enter search keyword')
        keyword_layout.addWidget(self.keyword_input)

        # Global Search Button
        global_search_btn = QPushButton('Search All Windows')
        global_search_btn.clicked.connect(self.start_global_search)
        keyword_layout.addWidget(global_search_btn)

        main_layout.addLayout(keyword_layout)

        # Search Windows Section
        self.search_windows_layout = QHBoxLayout()
        main_layout.addLayout(self.search_windows_layout)

        # Results Table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels([
            'Window', 'File Path', 'Matches', 'Processing Time (s)'
        ])
        main_layout.addWidget(self.results_table)

        # Overall Results
        self.overall_results = QTextEdit()
        self.overall_results.setReadOnly(True)
        main_layout.addWidget(self.overall_results)

    def create_search_windows(self):
        """
        Create search windows based on user input
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

    def start_global_search(self):
        """
        Start search across all windows
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

        # Track search start time
        global_start_time = time.time()

        # Create search threads
        self.search_threads = []
        for i, filepath in enumerate(self.file_paths):
            if filepath:  # Only create thread for windows with selected files
                thread = SearchThread(filepath, keyword, i+1)
                thread.search_complete.connect(self.process_search_result)
                thread.start()
                self.search_threads.append(thread)

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
        
        # Matches (display the total count of keyword occurrences)
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
        if result['matches']:
            overall_result_text.append("\nMatches:")
            overall_result_text.append("\n".join(result['matches']))  # Add the matches here only once

        overall_result_text.append("-" * 50)  # Separator line

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