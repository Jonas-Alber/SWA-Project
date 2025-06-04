# filepath: main.py
import os
from src.pipeline.pipeline import Pipeline, Stage, StageConfigElement, StepPipeline
from src.stages.tester import ArucoMarkerWallLineTester
# Import the new stages
from PIL import Image
from src.stages.loading import FileLoaderFactory
from src.stages.transformer import ArucoMarkerTransformer
from src.stages.consumer import PySide6Consumer, PySide6WidgetConsumer
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QSizePolicy

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel,
    QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton
)
def get_Stages():
    """Returns a list of stages to be used in the pipeline."""
    script_dir = os.path.dirname(__file__) 
    posterImage = os.path.join(script_dir, 'src', 'data', 'poster.jpg')
    posterImage = Image.open(posterImage)
    return [
        FileLoaderFactory(),
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

class StageConfigWidget(QWidget):
    def __init__(self, stage):
        super().__init__()
        self._stage: Stage = stage
        self._widgets = {}    # map each config element to its input widget
        self._elements = self._stage.getConfigElements()

        # Layouts
        main_layout = QVBoxLayout(self)

        # ◀︎ add stage name above the settings
        stage_name = stage.__class__.__name__
        title_label = QLabel(f"Stage: {stage_name}")
        main_layout.addWidget(title_label)

        form_layout = QFormLayout()
        main_layout.addLayout(form_layout)

        # Create input widget per config element
        for elem in self._elements:
            elem: StageConfigElement
            label = QLabel(elem.text)
            dtype = elem.data_type
            value = elem.data

            if dtype is int:
                widget = QSpinBox()
                widget.setRange(-1_000_000_000, 1_000_000_000)
                widget.setValue(int(value) if value != "" else 0)
            elif dtype is float:
                widget = QDoubleSpinBox()
                widget.setRange(-1e9, 1e9)
                widget.setValue(float(value) if value != "" else 0.0)
            elif dtype is bool:
                widget = QCheckBox()
                widget.setChecked(bool(value))
            else:  # default to string
                widget = QLineEdit()
                widget.setText(str(value))

            form_layout.addRow(label, widget)
            self._widgets[elem] = widget

        # Save button
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._on_save)
        main_layout.addWidget(save_btn)

    def _on_save(self):
        updated = []
        for elem, widget in self._widgets.items():
            elem: StageConfigElement
            dtype = elem.data_type
            if dtype is int:
                elem.data = widget.value()
            elif dtype is float:
                elem.data = widget.value()
            elif dtype is bool:
                elem.data = widget.isChecked()
            else:
                elem.data = widget.text()
            updated.append(elem)
        # apply changes to the stage
        self._stage.setConfigElements(updated)


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
        config_panel = QWidget()
        config_layout = QVBoxLayout(config_panel)
        for stage in stages:
            try:
                elems = stage.getConfigElements()
            except AttributeError:
            # stage has no getConfigElements → show its info
                widget = StageInfoWidget(stage)
            else:
                if elems:
                    widget = StageConfigWidget(stage)
                else:
                    # no config elements → skip or show info as you prefer
                    continue
            config_layout.addWidget(widget)
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