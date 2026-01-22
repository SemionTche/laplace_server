'''
LAPLACE-LHC server package.

Provides a ZMQ-based server, protocol definitions, validation utilities,
handlers, and PyQt6 signal controller.
'''
# libraries
from importlib.metadata import version, PackageNotFoundError


try:
    __version__ = version("laplace-server")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "__version__"
]

