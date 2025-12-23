from PyQt6.QtCore import QObject, pyqtSignal, Qt, QMetaObject

class ServerController(QObject):
    saving_path_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

    def on_server_save_path(self, path: str):
        # Safe cross-thread delivery
        QMetaObject.invokeMethod(
            self,
            lambda: self.saving_path_changed.emit(path),
            Qt.ConnectionType.QueuedConnection
        )
