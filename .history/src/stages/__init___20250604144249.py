# filepath: src/stages/__init__.py
from .stage_a import StageA # Keep existing if needed
from .calculate_total_sale_stage import CalculateTotalSaleStage
from .filter_electronics_stage import FilterElectronicsStage
from .save_output_stage import SaveOutputStageToConsole, SaveOutputStageToFile