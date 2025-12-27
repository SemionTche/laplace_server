# serverController.py
from PyQt6.QtCore import QObject, pyqtSignal

class ServerController(QObject):
    saving_path_changed = pyqtSignal(str)
    position_changed = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)

    def on_server_save_path(self, path: str):
        self.saving_path_changed.emit(path)
    
    def on_position_changed(self, positions: list):
        self.position_changed.emit(positions)