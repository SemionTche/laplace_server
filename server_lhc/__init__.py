'''
LAPLACE-LHC server package.

Provides a ZMQ-based server, protocol definitions, validation utilities,
handlers, and PyQt6 signal controller.
'''
# libraries
from importlib.metadata import version, PackageNotFoundError

# project
from .serverLHC import ServerLHC
from .serverController import ServerController
from . import protocol
from . import validations
from . import handlers

try:
    __version__ = version("laplace-server")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "ServerLHC",
    "ServerController",
    "protocol",
    "validations",
    "handlers",
    "__version__"
]

