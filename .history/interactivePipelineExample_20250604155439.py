# filepath: main.py
import os
from src.pipeline.pipeline import Pipeline, Stage, StageConfigElement, StageState, StepPipeline
from src.stages.tester import ArucoMarkerWallLineTester
# Import the new stages
from PIL import Image
from src.stages.loading import FileLoaderFactory
from src.stages.transformer import ArucoMarkerTransformer, CnnChairTransformer
from src.stages.consumer import PySide6Consumer, PySide6WidgetConsumer
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QSizePolicy

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel,
    QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton
)

from stageConfigWidget import StageConfigWidget
from PySide6.QtWidgets import QScrollArea

def get_Stages():
    """Returns a list of stages to be used in the pipeline."""
    script_dir = os.path.dirname(__file__) 
    posterImage = os.path.join(script_dir, 'src', 'data', 'poster.jpg')
    posterImage = Image.open(posterImage)
    return [
        FileLoaderFactory(),
        CnnChairTransformer(),
        ArucoMarkerWallLineTester(),
        ArucoMarkerTransformer(posterImage),
    ]
    
class StageInfoWidget(QWidget):
        def __init__(self, stage):
            super().__init__()
            self._stage = stage

            # Horizontal layout to display the stage name
            layout = QHBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)

            # Derive a display name (hier Klassename)
            stage_name = stage.__class__.__name__
            name_label = QLabel(f"Stage: {stage_name}")
            layout.addWidget(name_label)



class MainWindow(QMainWindow):
    def __init__(self, pipeline, display_widget, input_path, stages):
        super().__init__()
        self.pipeline = pipeline
        self.input_path = input_path
        self.setWindowTitle("Pipeline Viewer")

        # we need a horizontal layout

        # Central widget & main layout
        central = QWidget(self)
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # Left panel: one StageConfigWidget per stage, in order
        # … inside MainWindow.__init__(), replacing your $SELECTION_PLACEHOLDER$ block:

        # create a scroll area for the config panel
        config_scroll = QScrollArea()
        config_scroll.setWidgetResizable(True)

        # the actual panel that holds all StageConfigWidget / StageInfoWidget
        config_panel = QWidget()
        config_scroll.setWidget(config_panel)

        config_layout = QVBoxLayout(config_panel)
        for stage in stages:
            try:
                elems = stage.getConfigElements()
            except AttributeError:
                # stage has no config → just show its info
                widget = StageInfoWidget(stage)
            else:
                if elems:
                    widget = StageConfigWidget(stage)
                else:
                    # no config elements → skip or show info
                    continue
            config_layout.addWidget(widget)

        config_layout.addStretch()
        main_layout.addWidget(config_scroll, 1)
        config_layout.addStretch()
        main_layout.addWidget(config_panel, 1)

        # Right panel: display widget + Run button

        display_panel = QWidget()
        display_layout = QVBoxLayout(display_panel)

        # make the image expand to fill all available space
        display_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        display_layout.addWidget(display_widget, 1)

        # Run‐Button fixed to 40px height
        run_btn = QPushButton("Run")
        run_btn.setFixedHeight(40)
        run_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        run_btn.clicked.connect(self.on_run)
        display_layout.addWidget(run_btn, 0)

        main_layout.addWidget(display_panel, 3)

    def on_run(self):
        self.pipeline.run(self.input_path)


def main():
    app = QApplication([])

    script_dir = os.path.dirname(__file__)
    input_csv_path = os.path.join(script_dir, 'src', 'data', '20221115_113319.jpg')

    # build the list of stages (in order)
    stage_list = get_Stages()

    # create pipeline and add all stages
    pipeline = StepPipeline()
    for stage in stage_list:
        pipeline.add_stage(stage)

    # create & add the display/consumer stage
    displayWidget = PySide6WidgetConsumer()
    pipeline.add_stage(displayWidget)
    stage_list.append(displayWidget)

    # launch main window
    window = MainWindow(pipeline, displayWidget, input_csv_path, stage_list)
    window.resize(800, 600)
    window.show()

    app.exec()

if __name__ == "__main__":
    main()