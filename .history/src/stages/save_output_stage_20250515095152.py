# filepath: src/stages/save_output_stage.py
import json # Or import csv to write to a new CSV

class SaveOutputStageToConsole:
    def process(self, data):
        """Simulates saving the processed data by printing it."""
        # In a real scenario, you might write to a DB or file here.
        print("\n--- Processed Data (Simulated Save) ---")
        if data:
            # Print first 5 rows as an example
            print(json.dumps(data[:5], indent=2)) 
            print(f"(Total {len(data)} processed rows)")
        else:
            print("No data to save.")
        print("--- End of Processed Data ---")
        # Return the data if subsequent stages might need it, 
        # otherwise return None or a status message.
        return data 
    
class SaveOutputStageToFile:
    def __init__(self, filepath="output.json"):
        """Initialize with the path where the file should be saved."""
        self.filepath = filepath
        
    def process(self, data):
        """Saves the processed data to a file."""
        print(f"\n--- Saving processed data to {self.filepath} ---")
        if data:
            try:
                with open(self.filepath, 'w') as file:
                    json.dump(data, file, indent=2)
                print(f"Successfully saved {len(data)} records to {self.filepath}")
            except Exception as e:
                print(f"Error saving data to file: {e}")
        else:
            print("No data to save.")
        
        return data