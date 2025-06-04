# filepath: src/stages/load_csv_stage.py
from .abcFileLoader import FileLoader
from ...pipeline import PipeDataClass
import os
from PIL import Image
import numpy as np

class LoadPngStage(FileLoader):
    def process(self, file_path) -> PipeDataClass:
        """Loads an image from a JPG file using PIL, wraps it in a PipeDataClass."""
        if not os.path.exists(file_path):
            print(f"Error: File not found at {file_path}")
            return None

        try:
            with Image.open(file_path) as img:
                img_rgb = img.convert("RGBA")
                image_array = np.array(img_rgb)

            print(f"Successfully loaded image from {file_path}")
            # hier zurückgeben, was jetzt erwartet wird:
            image_array = Image.fromarray(image_array)
            return PipeDataClass(base_image=image_array)

        except Exception as e:
            print(f"Error reading JPG file {file_path}: {e}")
            return None

