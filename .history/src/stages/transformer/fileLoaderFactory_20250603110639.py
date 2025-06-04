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
        # Add more conditions here for other file types in the future
        # elif file_extension == '.json':
        #     return JsonFileLoader()
        else:
            raise ValueError(f"Unsupported file extension: {file_extension}")

# Example Usage (optional, can be removed or placed elsewhere)
if __name__ == '__main__':
    try:
        csv_loader = FileLoaderFactory.get_file_loader("data.csv")
        print(f"Loader for .csv: {type(csv_loader)}")
        # This will raise an error
        # json_loader = FileLoaderFactory.get_file_loader("data.json")
    except ValueError as e:
        print(e)
    except ImportError:
         # Mock CsvFileLoader if it doesn't exist for the example
        class CsvFileLoader:
            pass
        csv_loader = FileLoaderFactory.get_file_loader("data.csv")
        print(f"Loader for .csv (mocked): {type(csv_loader)}")
        try:
             # This will raise an error
            other_loader = FileLoaderFactory.get_file_loader("data.txt")
        except ValueError as e:
            print(e)
