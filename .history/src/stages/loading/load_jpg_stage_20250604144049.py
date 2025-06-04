# filepath: src/stages/load_csv_stage.py
from .abcFileLoader import FileLoader
from ...pipeline import PipeDataClass
import os
from PIL import Image
import numpy as np

class LoadJpgStage(FileLoader)->PipeDataClass:
    def process(self, file_path):
        """Loads an image from a JPG file using PIL, returns a NumPy array usable by cv2 or other libs."""
        if not os.path.exists(file_path):
            print(f"Error: File not found at {file_path}")
            return None
        try:
            with Image.open(file_path) as img:
                img_rgb = img.convert("RGB")
                image_array = np.array(img_rgb)
            print(f"Successfully loaded image from {file_path}")
            return image_array
        except Exception as e:
            print(f"Error reading JPG file {file_path}: {e}")
            return None
