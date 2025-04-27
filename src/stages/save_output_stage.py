# filepath: src/stages/save_output_stage.py
import json # Or import csv to write to a new CSV

class SaveOutputStage:
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