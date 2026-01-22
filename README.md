# LAPLACE Server (LAPLACE-LHC)

ZMQ-based server for the **LAPLACE-LHC** project.

This package provides a lightweight, command-driven server running in its own
thread, designed to exchange structured messages with clients using a defined
protocol. It is independent from GUI frameworks, while still allowing seamless
integration with PyQt through callback-based controllers.

---

## Features

- ZMQ-based TCP server
- Runs in its own non-daemon thread
- Protocol-based message validation and dispatching
- Configurable command callbacks
- Optional PyQt6 signal integration (without QObject inheritance)
- Clear separation between protocol, validation, and handlers

---

## Installation

From PyPI:

```bash
pip install laplace-server
```

Or from source (editable mode):

```bash
git clone https://github.com/<your-org>/laplace_server.git
cd laplace_server
pip install -e .
```

---

## Basic Usage

### Start a server

```python
from laplace_server import ServerLHC

server = ServerLHC(
    name="my_server",
    address="tcp://*:5555",
    freedom=2,
    device="motor"
)

server.start()
```

---

### Update server data

```python
server.set_data({"x": 1.2, "y": 3.4})
```

The stored data is transmitted when a `CMD_GET` request is received.

---

### Stop the server

```python
server.stop()
```

⚠️ The server runs in its own **non-daemon thread** and must be explicitly
stopped to allow the Python process to exit cleanly.

---

## PyQt6 Integration

The server does **not** inherit from `QObject`.
Instead, callbacks can be connected to a `ServerController`, which emits PyQt6
signals.

```python
from laplace_server import ServerLHC, ServerController

server = ServerLHC(...)
controller = ServerController()

server.set_on_get(controller.on_get)
server.set_on_opt(controller.on_opt)
```

This design keeps the server independent from PyQt while remaining GUI-friendly.

---

## Project Structure

```
laplace_server/
├── serverLHC.py         # Main server implementation
├── serverController.py  # PyQt6 signal controller
├── protocol.py          # Protocol constants and helpers
├── validations.py       # Input and message validation utilities
├── handlers/            # Command handlers
└── __init__.py
```

---

## Versioning

- `__version__`
  Package release version (matches the PyPI version).

- `PROTOCOL_VERSION`
  Internal communication protocol version, used to validate messages and ensure
  compatibility between clients and servers.

These two versions are intentionally independent.

---

## Error Handling Philosophy

- Validation functions return **human-readable error messages** or `None`
- Errors are logged, not raised, for expected runtime issues
- The server decides how to react (reply with error, ignore, continue)

This approach is suited for long-running network services.

---

## License

GPL-3.0

---

## Status

This project is actively used within the LAPLACE-LHC ecosystem and is intended
for controlled environments rather than general-purpose networking.
