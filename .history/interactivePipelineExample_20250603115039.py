# filepath: main.py
import os
from src.pipeline.pipeline import Pipeline
# Import the new stages
from PIL import Image
from src.stages.loading import FileLoaderFactory
from src.stages.transformer import ArucoMarkerTransformer
from src.stages.consumer import PySide6Consumer, PySide6WidgetConsumer

def get_Stages():
    """Returns a list of stages to be used in the pipeline."""
    script_dir = os.path.dirname(__file__) 
    posterImage = os.path.join(script_dir, 'src', 'data', 'poster.jpg')
    posterImage = Image.open(posterImage)
    return [
        FileLoaderFactory(),
        ArucoMarkerTransformer(posterImage),
    ]

def main():
    displayWidget = PySide6WidgetConsumer()
    # Define the path to the source data relative to this script
    # Assuming main.py is in the root directory SWA-Project/
    script_dir = os.path.dirname(__file__) 
    input_csv_path = os.path.join(script_dir, 'src', 'data', '20221115_113319.jpg')

    # Initialize the pipeline
    pipeline = Pipeline()
    
    posterImage = os.path.join(script_dir, 'src', 'data', 'poster.jpg')
    posterImage = Image.open(posterImage)
    arucoMarkerTransf = ArucoMarkerTransformer(posterImage)

    # Add stages to the pipeline in order
    pipeline.add_stage(FileLoaderFactory())
    pipeline.add_stage(arucoMarkerTransf)
    pipeline.add_stage(PySide6Consumer()) # Add the saving/output stage

    # Execute the pipeline with the input file path
    # The LoadCsvStage will use this path
    print(f"Starting pipeline with input file: {input_csv_path}")
    final_output = pipeline.run(input_csv_path)

    # The final output depends on the last stage. 
    # SaveOutputStage currently returns the data.
    print("\nPipeline execution finished.")
    # You could add further processing here if needed based on final_output


if __name__ == "__main__":
    main()