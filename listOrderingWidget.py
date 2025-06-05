from PySide6.QtWidgets import (
    QApplication, QLabel, QPushButton,
    QWidget, QListWidget, QListWidgetItem,
    QAbstractItemView, QVBoxLayout
)
from PySide6.QtCore import Qt
import sys

class ListOrderingWidget(QWidget):
    """
    Ein QWidget, das eine Liste von Widgets anzeigt
    und per Drag & Drop die Reihenfolge ändern lässt.
    """

    def __init__(self, widgets: list, parent=None):
        super().__init__(parent)
        self._init_ui(widgets)

    def _init_ui(self, widgets: list):
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget(self)
        # Drag & Drop innerhalb der Liste aktivieren
        self.list_widget.setDragEnabled(True)
        self.list_widget.setAcceptDrops(True)
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.MoveAction)

        for w in widgets:
            item = QListWidgetItem(self.list_widget)
            item.setSizeHint(w.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, w)

        layout.addWidget(self.list_widget)
        self.setLayout(layout)

    def get_ordered_widgets(self) -> list:
        """
        Gibt die Widgets in der aktuellen Reihenfolge zurück.
        """
        ordered = []
        for idx in range(self.list_widget.count()):
            item = self.list_widget.item(idx)
            w = self.list_widget.itemWidget(item)
            ordered.append(w)
        return ordered

# Beispielnutzung
if __name__ == "__main__":
    app = QApplication(sys.argv)

    widgets = [
        QLabel("Erstes Label"),
        QPushButton("Zweiter Button"),
        QLabel("Drittes Label"),
    ]

    lo_widget = ListOrderingWidget(widgets)
    lo_widget.resize(300, 200)
    lo_widget.show()

    def print_order():
        ordered = lo_widget.get_ordered_widgets()
        print([w.text() for w in ordered if hasattr(w, "text")])

    app.aboutToQuit.connect(print_order)
    sys.exit(app.exec())
