# filepath: src/stages/load_csv_stage.py
import os
from PIL import Image
import numpy as np

class LoadPngStage(FileLoader):
    def process(self, image:Image)-> Image:
        ...
