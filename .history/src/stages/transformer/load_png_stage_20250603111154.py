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
        ...
