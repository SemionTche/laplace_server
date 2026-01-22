'''
PyQt6 signal controller for the LAPLACE-LHC server.

This module defines the ServerController class, a QObject that provides
ready-to-use signals corresponding to server events. It allows a ServerLHC
instance to emit PyQt6 signals via simple callback methods, without requiring
the server itself to inherit from QObject.
'''

# libraries
try:
    from PyQt6.QtCore import QObject, pyqtSignal
except ModuleNotFoundError as e:
    raise ModuleNotFoundError(
        "PyQt6 is required for ServerController. "
        "Install with: pip install laplace-server[qt]"
    ) from e


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


    def on_position_changed(self, positions: list) -> None:
        '''Emit a 'positions' list.'''
        self.position_changed.emit(positions)


    def on_get(self) -> None:
        '''Emit a signal.'''
        self.get_received.emit()


    def on_opt(self, data: dict) -> None:
        '''Emit a 'data' dictionary.'''
        self.opt_received.emit(data)