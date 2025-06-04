# filepath: main.py
import os
from src.pipeline.pipeline import Pipeline
# Import the new stages
from PIL import Image
from src.stages.loading import FileLoaderFactory
from src.stages.transformer import ArucoMarkerTransformer
from src.stages.consumer import PySide6Consumer, PySide6WidgetConsumer
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton
def get_Stages():
    """Returns a list of stages to be used in the pipeline."""
    script_dir = os.path.dirname(__file__) 
    posterImage = os.path.join(script_dir, 'src', 'data', 'poster.jpg')
    posterImage = Image.open(posterImage)
    return [
        FileLoaderFactory(),
        ArucoMarkerTransformer(posterImage),
    ]


class MainWindow(QMainWindow):
    def __init__(self, pipeline, display_widget, input_path):
        super().__init__()
        self.pipeline = pipeline
        self.input_path = input_path
        self.setWindowTitle("Pipeline Viewer")
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Add the consumer's widget to the layout
        layout.addWidget(display_widget)

        # Add a Run button below
        run_button = QPushButton("Run")
        run_button.clicked.connect(self.on_run)
        layout.addWidget(run_button)

    def on_run(self):
        self.pipeline.run(self.input_path)

def main():
    # Qt application
    app = QApplication([])

    # Determine script directory and input path
    script_dir = os.path.dirname(__file__) 
    input_csv_path = os.path.join(script_dir, 'src', 'data', '20221115_113319.jpg')

    # Build the pipeline
    pipeline = Pipeline()
    for stage in get_Stages():
        pipeline.add_stage(stage)

    # Create the PySide6 widget consumer and add to pipeline
    displayWidget = PySide6WidgetConsumer()
    pipeline.add_stage(displayWidget)

    # Create and show main window
    window = MainWindow(pipeline, displayWidget, input_csv_path)
    window.resize(800, 600)
    window.show()

    app.exec()

if __name__ == "__main__":
    main()