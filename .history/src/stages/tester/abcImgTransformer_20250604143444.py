import abc
from PIL import Image
from ...pipeline.pipeline import Stage, StageConfigElement

class AbcImageTester(Stage):
    """Abstract base class for file loading stages."""

    def process(self, original_image: Image) -> Image:
        """
        Loads data from a specified file path.

        Args:
            file_path: The path to the file to be loaded.

        Returns:
            A list of dictionaries, where each dictionary represents a row
            of data, or an empty list if loading fails or the file is empty.
        """
        raise NotImplementedError("Subclasses must implement the process method.")
