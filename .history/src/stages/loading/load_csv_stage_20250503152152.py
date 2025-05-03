# filepath: src/stages/load_csv_stage.py
from .abcFileLoader import FileLoader
import csv
import os

class LoadCsvStage:
    def process(self, file_path):
        """Loads data from a CSV file."""
        if not os.path.exists(file_path):
            print(f"Error: File not found at {file_path}")
            return []
        data = []
        try:
            with open(file_path, mode='r', encoding='utf-8') as infile:
                reader = csv.DictReader(infile)
                # Skip empty rows or rows with potential issues if needed
                data = [row for row in reader if row] 
            print(f"Loaded {len(data)} rows from {file_path}")
            return data
        except Exception as e:
            print(f"Error reading CSV file {file_path}: {e}")
            return [] # Return empty list on error