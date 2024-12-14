import os
import time
import threading
from typing import List, Optional, Tuple

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
