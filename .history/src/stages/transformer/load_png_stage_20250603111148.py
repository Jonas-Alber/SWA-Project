# filepath: src/stages/load_csv_stage.py
from .abcImgTransformer import AbcImageTransformer
import os
from PIL import Image
import numpy as np

class ArucoMarkerDetector(AbcImageTransformer):
    def __init__(self, poster_image: Image):
        """_summary_

        Args:
            file_path (str): _description_
        """
        self._poster_image = poster_image
    def process(self, image:Image)->Image:
        """Loads an image from a PNG file using PIL, returns a NumPy array usable by cv2 or other libs."""
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
            print(f"Error reading PNG file {file_path}: {e}")
            return None
