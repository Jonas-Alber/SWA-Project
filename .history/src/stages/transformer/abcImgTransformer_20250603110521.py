import abc
from PIL import Image

class AbcImageTransformer(abc.ABC):
    """Abstract base class for file loading stages."""

    @abc.abstractmethod
    def process(self, img_data: Image) -> Image:
        """
        Loads data from a specified file path.

        Args:
            file_path: The path to the file to be loaded.

        Returns:
            A list of dictionaries, where each dictionary represents a row
            of data, or an empty list if loading fails or the file is empty.
        """
        pass