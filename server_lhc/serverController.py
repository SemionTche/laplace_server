# libraries
from PyQt6.QtCore import QObject, pyqtSignal

class ServerController(QObject):
    saving_path_changed = pyqtSignal(str)
    position_changed = pyqtSignal(list)
    get_received = pyqtSignal()
    opt_received = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

    def on_server_save_path(self, path: str):
        self.saving_path_changed.emit(path)
    
    def on_position_changed(self, positions: list):
        self.position_changed.emit(positions)
    
    def on_get(self):
        self.get_received.emit()
    
    def on_opt(self, data):
        self.opt_received.emit(data)