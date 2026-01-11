# WebSocket Device Monitor & OTA Manager  
### *Real-Time Memory Inspection, Dynamic Tuning & Secure Firmware Updates*

[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/downloads/) [![PyQt5](https://img.shields.io/badge/GUI-PyQt5-green)](https://www.riverbankcomputing.com/software/pyqt/) [![WebSocket](https://img.shields.io/badge/Protocol-WebSocket-orange)](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API) [![OTA Ready](https://img.shields.io/badge/OTA-Ready-brightgreen)](#) [![ELF Parser](https://img.shields.io/badge/ELF-pyelftools-purple)](#)

---

**A full-stack embedded debugging and deployment suite** — monitor live variables, write to memory on-the-fly, and push firmware updates over WebSocket. Built for developers working with STM32, ESP32, or any MCU with WebSocket/XCP-like capabilities.

---

## Core Capabilities

- **Live Memory Monitoring** – Poll scalar/array variables at 100+ Hz  
- **Instant Write Access** – Modify RAM values directly from GUI  
- **OTA Firmware Flashing** – Chunked, verified, resumable updates  
- **ELF to CSV Auto-Mapping** – Extract symbols & generate memory maps  
- **Multi-Client WebSocket Server** – Thread-safe, JSON-based protocol  
- **Interactive PyQt5 Dashboard** – Plots, tables, logs, and export tools  

---

## Technologies

| Layer               | Technology                                  |
|---------------------|---------------------------------------------|
| **Language**        | Python 3.8+                                 |
| **GUI**             | PyQt5 + pyqtgraph (live plotting)           |
| **Networking**      | `websocket-server` (async-ready)            |
| **ELF Parsing**     | `pyelftools` (DWARF introspection)          |
| **Data Handling**   | `pandas`, `numpy`, `csv`                    |
| **Logging**         | Custom colored + rotating file logger       |
| **Threading**       | `threading`, `concurrent.futures`, `queue`  |
| **File System**     | `pathlib` (modern path handling)            |

---

## Project Structure

```
.
├── main.py                  # Launch GUI
├── src/
│   ├── server.py            # WebSocket server + protocol engine
│   ├── gui.py               # Full PyQt5 interface (tabs, graphs, OTA)
│   ├── json_handler.py      # JSON command/response parser
│   ├── ota_handler.py       # Firmware transfer & verification logic
│   ├── mem_map_byelf.py     # .elf → .csv variable extractor
│   ├── logger_config.py     # Colorful + rotating logs
│   └── testpath.py          # Path verification tool
├── data/elf/                # Input firmware binaries
├── data/csv/                # Generated memory maps
├── logs/                    # Auto-rotating log files
```

---

## Quick Start

```bash
git clone https://github.com/yourusername/websocket-device-monitor.git
cd websocket-device-monitor
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 1. Generate Memory Map
```bash
python src/mem_map_byelf.py
# → data/csv/XCP_slave_disco_*.csv
```

### 2. Launch Application
```bash
python main.py
```

---

## JSON Protocol (Device ↔ Server)

```json
// Initialize debug session
{"cmd": "init", "con_id": "01"}

// Read 32-bit value
{"cmd": "mem_read", "add": "0x20000100", "size": "32"}

// Write value (auto-converted to binary)
{"cmd": "mem_write", "add": "0x20000100", "size": "32", "data": "0b00000000000000000000000000001010"}

// Terminate session
{"cmd": "end", "con_id": "01"}
```

**Responses**:
```json
{"res": "mem_read", "add": "0x20000100", "value": "42"}
{"res": "mem_write", "state": "success"}
```

---

## GUI Highlights

- **Monitoring Tab** – Live plots + editable table  
- **OTA Tab** – Select `.bin`, view progress, cancel anytime  
- **Log Console** – Real-time, filterable, color-coded  
- **Export** – CSV or Excel with timestamps  

---

## Development & Contribution

```bash
# Run tests
python -m unittest discover

# Add feature → test → PR
```

We welcome:
- New data type support (`float`, `double`, structs)
- Protocol extensions (streaming, events)
- GUI themes & accessibility
- Dockerization

---

## Debugging

- Logs: `logs/WebSocketServer_*.log`
- Enable debug: Edit `logger_config.py` → `log_level=logging.DEBUG`
- Path issues? Run `python src/testpath.py`

---

**Precision control for embedded systems — monitor, tune, update, repeat.**  
*No JTAG. No serial. Just WebSocket magic.*





# XCP SPI WebSocket Gateway

A lightweight **XCP master gateway** running on a **Raspberry Pi** that enables **remote, non-intrusive runtime memory read/write** on embedded targets (e.g., STM32) over **SPI**, controlled via **WebSocket**.

---

## ✨ Key Features

* WebSocket-based remote access (works over ngrok)
* SPI-based XCP master implementation
* Runtime memory **read / write** (8, 16, 32-bit)
* Uses XCP commands: `SET_MTA`, `SHORT_UPLOAD`, `DOWNLOAD`
* Suitable for debugging, calibration, and FYP projects

---

## 🧩 Architecture

```
Web Client → WebSocket → Raspberry Pi (Gateway) → SPI/XCP → STM32 Target
```

---

## 🛠 Requirements

**Hardware**

* Raspberry Pi with SPI enabled
* XCP-enabled embedded target (STM32)

**Software**

* Python 3.8+
* `websocket-client`, `spidev`

```bash
pip install websocket-client spidev
```

---

## 📡 Supported Commands

### Init

```json
{ "cmd": "init", "con_id": "01" }
```

### Memory Read

```json
{ "cmd": "mem_read", "add": "0x20000050", "size": "32" }
```

### Memory Write

```json
{ "cmd": "mem_write", "add": "0x20000050", "size": "8", "data": "0b00010101" }
```

---

## 🔐 Notes

* Use valid memory addresses only
* Intended for development and debugging, not production






# XCP Slave (SPI) – Embedded Target

This project implements an **XCP (Universal Measurement and Calibration Protocol) Slave** on an **embedded microcontroller (e.g., STM32)** using **SPI** as the transport layer.

It is designed to work with an external **XCP Master / Gateway** (such as a Raspberry Pi) to allow **non-intrusive runtime memory read and write** for debugging, monitoring, and calibration.

---

## ✨ Key Features

* XCP Slave implementation over **SPI**
* Supports **runtime memory read & write**
* Non-intrusive access (no firmware halt)
* Compatible with XCP Master running on Raspberry Pi
* Suitable for **remote debugging** and **final-year projects**

---

## 🧩 System Architecture

```
XCP Master (PC / Cloud / Raspberry Pi)
        │
        │ WebSocket / SPI
        ▼
Raspberry Pi (Gateway)
        │ SPI (XCP DTOs)
        ▼
STM32 / Embedded Target (This Project)
```

---

## 📂 Project Structure

```
.
├── xcp.c        # Core XCP protocol handling
├── xcp.h        # XCP definitions and APIs
├── spi.c        # SPI transport layer
├── spi.h        # SPI interface definitions
├── main.c       # Application entry point
```

---

## 🛠 Requirements

### Hardware

* STM32 microcontroller (SPI-capable)
* SPI connection to XCP Master (Raspberry Pi or PC)

### Software

* STM32CubeIDE / GCC toolchain
* HAL or LL drivers enabled for SPI

---

## 🔧 Configuration

### SPI Settings (Must match XCP Master)

* Mode: SPI Mode 0
* Frame size: 8 bits
* Clock speed: Configurable (tested with ≤ 500 kHz)

---

## 📡 Supported XCP Commands

| Command      | Code | Description                 |
| ------------ | ---- | --------------------------- |
| CONNECT      | 0xFF | Establish XCP connection    |
| SET_MTA      | 0xF6 | Set memory transfer address |
| SHORT_UPLOAD | 0xF5 | Read memory at runtime      |
| DOWNLOAD     | 0xF0 | Write memory at runtime     |

---

## 🔄 Data Flow (Example: Memory Read)

1. Master sends `SET_MTA` with target address
2. Slave updates internal MTA pointer
3. Master sends `SHORT_UPLOAD`
4. Slave reads memory and responds with data

---

## 🔒 Safety Notes

* Ensure only valid RAM/Flash regions are accessed
* Invalid addresses may cause system faults
* Recommended to protect critical memory regions

---

## 🎓 Use Cases

* Remote embedded debugging
* Live firmware monitoring
* Calibration and parameter tuning
* Final Year / Research projects

---

## 📌 Limitations

* Block upload/download not implemented
* No authentication or memory protection layer
* Single-master operation

---


## 📄 License

MIT License

---

⭐ Designed to be used together with the **XCP SPI WebSocket Gateway** project.


---

## 📄 License

MIT License
