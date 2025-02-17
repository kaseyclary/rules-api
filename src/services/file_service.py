from functools import lru_cache
import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime

class FileService:
    _file_cache: Dict[str, dict] = {}
    _cache_timestamps: Dict[str, datetime] = {}
    _CACHE_DURATION = 3600  # 1 hour in seconds

    @staticmethod
    def read_json_file(file_path: str) -> dict:
        """
        Read and cache JSON file contents with timestamp-based expiration
        """
        current_time = datetime.now()
        
        # Check if cached and not expired
        if (file_path in FileService._file_cache and 
            (current_time - FileService._cache_timestamps[file_path]).total_seconds() < FileService._CACHE_DURATION):
            return FileService._file_cache[file_path]
        
        with open(file_path, 'r') as f:
            data = json.load(f)
            FileService._file_cache[file_path] = data
            FileService._cache_timestamps[file_path] = current_time
            return data

    @staticmethod
    @lru_cache(maxsize=32)
    def get_available_years(base_path: str, file_prefix: str) -> List[int]:
        """
        Get and cache available years from file names
        """
        pattern = f"{file_prefix}_*.json"
        files = Path(base_path).glob(pattern)
        years = []
        for file in files:
            try:
                year = int(file.stem.replace(file_prefix + "_", ""))
                years.append(year)
            except ValueError:
                continue
        return sorted(years) 