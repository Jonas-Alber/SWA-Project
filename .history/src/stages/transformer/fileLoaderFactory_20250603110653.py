import os

from .abcImgTransformer import AbcImageTransformer  # Assuming this is the base class for file loaders
from PIL import Image
#from .a import LoadPngStage  # Assuming PngFileLoader is in the same directory

class ImageTransformerFactory(AbcImageTransformer):
    
    def process(self, file_path):
        processor = self.get_file_loader(file_path)
        return processor.process(file_path)
    """
    Factory class to get the appropriate file loader based on the file extension.
    """
    @staticmethod
    def get_file_loader(image: Image)-> AbcImageTransformer:
        """
        Returns a file loader instance based on the file extension.

        Args:
            file_path: The path to the file.

        Returns:
            An instance of a file loader class.

        Raises:
            ValueError: If the file extension is not supported.
        """
        return LoadPngStage()
