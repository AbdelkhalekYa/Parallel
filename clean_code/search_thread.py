from PyQt5.QtCore import QThread, pyqtSignal
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
