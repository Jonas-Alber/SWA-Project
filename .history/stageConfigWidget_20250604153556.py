
class StageConfigWidget(QWidget):
    def __init__(self, stage):
        super().__init__()
        self._stage: Stage = stage
        self._stage.registerStateChangeCallback(self._onStateChangeCallback)
        self._widgets = {}    # map each config element to its input widget
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