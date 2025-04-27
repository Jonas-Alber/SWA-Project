# filepath: src/stages/filter_electronics_stage.py
class FilterElectronicsStage:
    def process(self, data):
        """Filters data to include only 'Electronics' category."""
        filtered_data = [row for row in data if row.get('Category') == 'Electronics']
        print(f"Filtered data to {len(filtered_data)} 'Electronics' rows.")
        return filtered_data