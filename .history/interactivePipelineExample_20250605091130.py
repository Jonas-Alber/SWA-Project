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
from listOrderingWidget import ListOrderingWidget
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel,
    QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton
)
from PySide6.QtCore import QThread, Signal, QTimer
from stageConfigWidget import StageConfigWidget
from PySide6.QtWidgets import QFileDialog, QHBoxLayout
import time
from PySide6.QtCore import Qt

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
    
class RunWorker(QThread):
    finished = Signal(object)   # Optional: liefert das Ergebnis zurück

    def __init__(self, pipeline, input_path):
        super().__init__()
        self.pipeline = pipeline
        self.input_path = input_path

    def run(self):
        result = self.pipeline.run(self.input_path)
        self.finished.emit(result)
        
class UpdateWorker(QThread):
    finished = Signal(object)   # Optional: liefert das Ergebnis zurück

    def __init__(self, pipeline):
        super().__init__()
        self.pipeline = pipeline

    def run(self):
        result = self.pipeline.update()
        self.finished.emit(result)
    
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

#Foto von <a href="https://unsplash.com/de/@pbernardon?utm_content=creditCopyText&utm_medium=referral&utm_source=unsplash">Pascal Bernardon</a> auf <a href="https://unsplash.com/de/fotos/menschen-die-tagsuber-auf-der-strasse-spazieren-gehen-3jlJjmMUjEA?utm_content=creditCopyText&utm_medium=referral&utm_source=unsplash">Unsplash</a>
      

class MainWindow(QMainWindow):
    def __init__(self, pipeline, display_widget, input_path, stages):
        super().__init__()
        self.pipeline = pipeline
        self.input_path = input_path
        self.setWindowTitle("Pipeline Viewer")
        # build a horizontal button‐bar with “Open” and “Run”
        self.button_bar = QHBoxLayout()
        self.button_bar.setContentsMargins(0, 0, 0, 0)
        # replace the HBox frontend with a VBox that stacks buttons above the label
        _vert = QVBoxLayout()
        _vert.setContentsMargins(0, 0, 0, 0)

        # inner HBox for the two buttons
        _btns = QHBoxLayout()
        _btns.setContentsMargins(0, 0, 0, 0)
        _vert.addLayout(_btns)

        # the status label under the buttons
        self._last_run_time = 0.0
        self._last_update_time = 0.0
        self._run_start_time = 0.0
        self._update_start_time = 0.0
        self.status_label = QLabel("")
        self.updateRunTime()
        self.status_label.setAlignment(Qt.AlignCenter)
        _vert.addWidget(self.status_label)

        # monkey‐patch so that subsequent .addWidget calls go into the inner HBox
        _vert.addWidget = _btns.addWidget

        # finally assign our stack to self.button_bar
        self.button_bar = _vert
        
        # timing placeholders
        
        # Open‐file button
        self.open_btn = QPushButton("Open…")
        self.open_btn.setFixedHeight(40)
        self.open_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.open_btn.clicked.connect(self.open_file)
        self.button_bar.addWidget(self.open_btn)

        # Run button (already calls on_run)
        self.run_btn = QPushButton("Update")
        self.run_btn.setFixedHeight(40)
        self.run_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.run_btn.clicked.connect(self.on_update)
        self.button_bar.addWidget(self.run_btn)
        # we need a horizontal layout
        # Timer für Live-Updates der Laufzeit
        self._timer = QTimer(self)
        self._timer.setInterval(100)  # alle 100 ms
        self._timer.timeout.connect(self._on_timer_tick)

        # Central widget & layouts: first the button bar, then the main panels
        central = QWidget(self)
        self.setCentralWidget(central)
        central_layout = QVBoxLayout(central)
        central_layout.addLayout(self.button_bar)
        main_layout = QHBoxLayout()
        central_layout.addLayout(main_layout)

        # Left panel: one StageConfigWidget per stage, in order
        config_panel = QWidget()
        config_layout = QVBoxLayout(config_panel)
        stageWidgetList = []
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
            stageWidgetList.append(widget)
            config_layout.addWidget(widget)
        config_layout.addStretch()
        main_layout.addWidget(config_panel, 1)
        main_layout.addWidget(self.list_ordering_widget, 1)

        # Right panel: display widget + Run button

        display_panel = QWidget()
        display_layout = QVBoxLayout(display_panel)

        # make the image expand to fill all available space
        display_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        display_layout.addWidget(display_widget, 1)
        main_layout.addWidget(display_panel, 3)
        self.run_btn.setEnabled(False)
        
        self._run_thread = None
        # verlinke den Button auf deine Instanz:
        self.run_btn.clicked.connect(self.on_update)

    def updateRunTime(self):
        self.status_label.setText(
            f"Last run: {self._run_start_time:.2f} s  Last update: {self._update_start_time:.2f} s"
        )
        
    def open_file(self):
        """Open a file dialog to select an image file."""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Image File", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.tiff);;All Files (*)", options=options)
        if file_name:
            self.input_path = file_name
            # Update the pipeline with the new input path
            self.on_run()

    def _on_timer_tick(self):
        # Wenn der Worker noch läuft, aktualisiere das Label
        if self._run_thread and self._run_thread.isRunning():
            elapsed = time.time() - self._startTime
            mode = "Run" if isinstance(self._run_thread, RunWorker) else "Update"
            self.status_label.setText(
                f"{mode}: {elapsed:.2f} s  Last run: {self._run_start_time:.2f} s  "
                f"Last update: {self._update_start_time:.2f} s"
            )
        else:
            # Thread ist fertig → Timer stoppen
            self._timer.stop()
            # abschließend das statische Update anzeigen
            self.updateRunTime()
            
    def on_update(self):
        if self._run_thread and self._run_thread.isRunning():
            return    # Verhindert mehrfaches Starten
        # Button deaktivieren, damit nicht nochmal gedrückt wird
        self.run_btn.setEnabled(False)
        self.open_btn.setEnabled(False)
        self._startTime = time.time()  # Startzeit für die Aktualisierung
        
        # Starte Worker-Thread
        self._run_thread = UpdateWorker(self.pipeline)
        self._run_thread.finished.connect(self._on_update_finished)
        self._timer.start()
        self._run_thread.start()
        
    def _on_update_finished(self, result):
        # Hier kannst du das Ergebnis verarbeiten / display_widget updaten
        self.run_btn.setEnabled(True)
        self.open_btn.setEnabled(True)
        self._update_start_time = time.time() - self._startTime  # Startzeit für die Aktualisierung
        self.updateRunTime()

    def on_run(self):
        if self._run_thread and self._run_thread.isRunning():
            return    # Verhindert mehrfaches Starten
        # Button deaktivieren, damit nicht nochmal gedrückt wird
        self.run_btn.setEnabled(False)
        self.open_btn.setEnabled(False)
        self._startTime = time.time() 
        
        # Starte Worker-Thread
        self._run_thread = RunWorker(self.pipeline, self.input_path)
        self._run_thread.finished.connect(self._on_run_finished)
        self._timer.start()
        self._run_thread.start()
        
    def _on_run_finished(self, result):
        # Hier kannst du das Ergebnis verarbeiten / display_widget updaten
        self.run_btn.setEnabled(True)
        self.open_btn.setEnabled(True)
        self._run_start_time = time.time() - self._startTime
        self.updateRunTime()


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