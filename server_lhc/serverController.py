# libraries
from PyQt6.QtCore import QObject, pyqtSignal


class ServerController(QObject):
    '''
    Helper class made to define signals to emit.
    '''

    # signals to emit
    saving_path_changed = pyqtSignal(str)
    position_changed = pyqtSignal(list)
    get_received = pyqtSignal()
    opt_received = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)


    def on_saving_path_changed(self, path: str) -> None:
        '''Emit a 'path' string.'''
        self.saving_path_changed.emit(path)


    def on_position_changed(self, position: list) -> None:
        '''Emit a 'position' list.'''
        self.position_changed.emit(position)


    def on_get(self) -> None:
        '''Emit a signal.'''
        self.get_received.emit()


    def on_opt(self, data: dict) -> None:
        '''Emit a 'data' dictionary.'''
        self.opt_received.emit(data)