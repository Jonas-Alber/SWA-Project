# filepath: src/stages/calculate_total_sale_stage.py
class CalculateTotalSaleStage:
    def process(self, data):
        """Calculates the total sale for each row."""
        processed_data = []
        for row in data:
            try:
                # Ensure UnitPrice and QuantitySold exist and are convertible
                unit_price = float(row.get('UnitPrice', 0))
                quantity_sold = int(row.get('QuantitySold', 0))
                row['TotalSale'] = unit_price * quantity_sold
                processed_data.append(row)
            except (ValueError, TypeError) as e:
                print(f"Skipping row due to data error: {row}. Error: {e}")
                # Optionally append row without TotalSale or skip entirely
                # processed_data.append(row) 
        print(f"Calculated TotalSale for {len(processed_data)} rows.")
        return processed_data