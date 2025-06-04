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


class StageConfigWidget(QWidget):
    def __init__(self, stage):
        super().__init__()
        self._stage: Stage = stage
        self._stage.registerStateChangeCallback(self._onStateChangeCallback)
        self._widgets = {}    # map each config element to its input widget or a dict of {key: checkbox_widget} for dict type
        self._elements = self._stage.getConfigElements()

        # Layouts
        main_layout = QVBoxLayout(self)
        self._main_layout = main_layout

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
                widget.setValue(int(value) if value is not None and str(value).strip() != "" else 0)
                form_layout.addRow(label, widget)
                self._widgets[elem] = widget
            elif dtype is float:
                widget = QDoubleSpinBox()
                widget.setRange(-1e9, 1e9)
                widget.setValue(float(value) if value is not None and str(value).strip() != "" else 0.0)
                form_layout.addRow(label, widget)
                self._widgets[elem] = widget
            elif dtype is bool:
                widget = QCheckBox()
                widget.setChecked(bool(value))
                form_layout.addRow(label, widget)
                self._widgets[elem] = widget
            elif dtype is dict:  # Assuming dict[str, bool]
                # Create a container widget for the dictionary items
                dict_widget_container = QWidget()
                dict_layout = QVBoxLayout(dict_widget_container)
                dict_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for tighter packing
                
                checkbox_map = {}
                if isinstance(value, dict):
                    for key_str, bool_val in value.items():
                        # Ensure the value is treated as a boolean for the checkbox state
                        cb = QCheckBox(str(key_str))
                        cb.setChecked(bool(bool_val))
                        dict_layout.addWidget(cb)
                        checkbox_map[str(key_str)] = cb
                
                form_layout.addRow(label, dict_widget_container)
                self._widgets[elem] = checkbox_map  # Store the map of {key_str: checkbox_widget}
            else:  # default to string
                widget = QLineEdit()
                widget.setText(str(value) if value is not None else "")
                form_layout.addRow(label, widget)
                self._widgets[elem] = widget
    def _onStateChangeCallback(self, state):
        # Hintergrundfarbe je nach StageState setzen
        if state == StageState.UNIITIALIZED:
            color = 'white'
        elif state == StageState.WAITING:
            color = 'lightgray'
        elif state == StageState.RUNNING:
            color = 'lightyellow'
        elif state == StageState.FINISHED:
            color = 'lightgreen'
        elif state == StageState.ERROR:
            color = 'lightcoral'
        else:
            color = 'white'

        # Objektname setzen, damit der Style nur auf diesen Container wirkt
        if not self.objectName():
            self.setObjectName("stageConfigContainer")

        # StyleSheet nur für das Container-Widget anwenden, nicht für die Kinder
        self.setStyleSheet(f"#{self.objectName()} {{ background-color: {color}; }}")

    def _on_save(self):
        updated = []
        for elem, widget_or_map in self._widgets.items():
            elem: StageConfigElement
            dtype = elem.data_type
            if dtype is int:
                elem.data = widget_or_map.value()
            elif dtype is float:
                elem.data = widget_or_map.value()
            elif dtype is bool:
                elem.data = widget_or_map.isChecked()
            elif dtype is dict:  # Assuming dict[str, bool]
                new_dict_val = {}
                checkbox_map = widget_or_map # This is the map stored in __init__
                for key_str, cb_widget in checkbox_map.items():
                    new_dict_val[key_str] = cb_widget.isChecked()
                elem.data = new_dict_val
            else:  # string
                elem.data = widget_or_map.text()
            updated.append(elem)
        # apply changes to the stage
        self._stage.setConfigElements(updated)