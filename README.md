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
git clone https://github.com/SemionTche/laplace_server.git
cd laplace_server
pip install -e .
```

---

## Basic Usage

### Start a server

```python
from laplace_server import ServerLHC
from laplace_server.protocol import DEVICE_MOTOR

server = ServerLHC(
    name="my_server",
    address="tcp://*:5555",
    freedom=2,
    device=DEVICE_MOTOR
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

## Protocol Overview

The server communicates using a lightweight, JSON-based message protocol over
ZMQ. Each message must follow a well-defined structure and include a protocol
version to ensure compatibility between clients and servers.

### Message Structure

All messages exchanged with the server must be JSON objects with the following
fields:

- `version` — Protocol version identifier
- `cmd` — Command name
- `from` — Sender identifier
- `payload` — Command-specific data (may be empty)

Example message:
```
{
  "version": "0.1.6",
  "cmd": "GET",
  "from": "client_1",
  "payload": {}
}
```

Messages that do not comply with this structure are rejected and may trigger an
error response from the server.

### Commands

The protocol defines a fixed set of commands used to interact with the server,
including:

- `CMD_INFO` — Request server information
- `CMD_PING` — Check server availability
- `CMD_GET` — Retrieve the server data
- `CMD_SET` — For motor realted server, set new positions
- `CMD_SAVE` — Indicate a saving path
- `CMD_OPT` — Send optimization-related data
- `CMD_STOP` — Request server shutdown

Each command is handled by a dedicated handler function on the server side.

### Protocol Versioning

The protocol version is defined by `laplace_server.protocolPROTOCOL_VERSION` and is 
validated for every incoming message. If a version mismatch is detected, the message 
is rejected to prevent undefined behavior.

The protocol version is independent from the package release version
(`__version__`) and is only updated when the message format or semantics change.

---

## PyQt6 Integration

The server does **not** inherit from `QObject`.
Instead, callbacks can be connected to a `ServerController`, which emits PyQt6
signals.

```python
from laplace_server import ServerLHC
from laplace_server.server_controller import ServerController

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
├── server_lhc.py         # Main server implementation
├── server_controller.py  # PyQt6 signal controller (optional)
├── protocol.py           # Protocol constants and helpers
├── validations.py        # Input and message validation utilities
├── handlers/             # Command handlers
└── __init__.py
```

---

## Versioning

- `laplace_server.__version__`
  Package release version (matches the PyPI version).

- `laplace_server..protocol.PROTOCOL_VERSION`
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
