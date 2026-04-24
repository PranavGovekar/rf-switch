# rf-switch

Python library for controlling two **H6P-330127 SP6T RF switches** via an
Arduino Nano Every running the companion firmware (`rf_switch_controller.ino`).

---

## Installation

```bash
pip install rf-switch
```

Or install from source:

```bash
git clone https://github.com/yourusername/rf-switch
cd rf-switch
pip install .
```

---

## Requirements

- Python 3.8+
- `pyserial` (installed automatically)
- Arduino Nano Every flashed with `rf_switch_controller.ino`

---

## Hardware Setup

| Switch | Arduino Pins       | Notes               |
|--------|--------------------|---------------------|
| SW1    | D2, D3, D4, D5, D6, D7 | Left side of board |
| SW2    | A0, A1, A2, A3, A4, A5 | Right side of board |

- Switch supply voltage: **22–26V DC** (separate from Arduino)
- Logic level: **TTL** (3.3V HIGH from Nano Every is compatible)
- **Common GND** between Arduino and switch is required

---

## Quick Start

```python
from rf_switch import RFSwitch

# Connect (replace with your actual port)
sw = RFSwitch('COM3')          # Windows
# sw = RFSwitch('/dev/ttyACM0')  # Linux

# Set channels
sw.set(1, 3)        # Switch 1 -> Channel 3
sw.set(2, 5)        # Switch 2 -> Channel 5

# Set both at once
sw.set_both(2, 4)   # SW1 -> CH2, SW2 -> CH4

# Query current state
print(sw.status())  # {'sw1': 2, 'sw2': 4}

# Park to safe default (CH6) and close
sw.close()
```

### Context Manager (Recommended)

Automatically parks both switches to CH6 and closes the port on exit,
even if your script crashes.

```python
from rf_switch import RFSwitch

with RFSwitch('COM3') as sw:
    sw.set(1, 1)
    sw.set(2, 6)
    print(sw.status())
# Port closed and switches parked to CH6 automatically
```

---

## API Reference

### `RFSwitch(port, baudrate=115200, timeout=2.0, boot_wait=2.0)`

Creates a connection to the Arduino.

| Parameter   | Type  | Default | Description                                      |
|-------------|-------|---------|--------------------------------------------------|
| `port`      | `str` | —       | Serial port, e.g. `'COM3'` or `'/dev/ttyACM0'`  |
| `baudrate`  | `int` | 115200  | Must match the Arduino sketch                    |
| `timeout`   | `float` | 2.0   | Serial read timeout in seconds                   |
| `boot_wait` | `float` | 2.0   | Seconds to wait for Arduino to boot on connect   |

---

### `sw.set(switch, channel) -> str`

Set a switch to a specific channel using one-hot encoding.

```python
sw.set(1, 3)   # Switch 1 -> Channel 3
sw.set(2, 6)   # Switch 2 -> Channel 6
```

| Parameter | Type  | Valid values |
|-----------|-------|-------------|
| `switch`  | `int` | `1` or `2`  |
| `channel` | `int` | `1` to `6`  |

Raises `ValueError` if arguments are out of range.  
Raises `RFSwitchError` if the Arduino returns an error.

---

### `sw.set_both(ch1, ch2)`

Set both switches in a single call.

```python
sw.set_both(2, 4)   # SW1 -> CH2, SW2 -> CH4
```

---

### `sw.default(switch=None)`

Park switch(es) to CH6 — the safe hardware default for the H6P-330127.

```python
sw.default()     # Both switches -> CH6
sw.default(1)    # Only Switch 1 -> CH6
sw.default(2)    # Only Switch 2 -> CH6
```

---

### `sw.status() -> dict`

Query the Arduino for the current channel state. Returns a dict.

```python
print(sw.status())   # {'sw1': 3, 'sw2': 5}
```

---

### `sw.channel -> dict`

Returns the locally cached state without a serial round-trip.
Use `status()` if you need to confirm directly from the Arduino.

```python
print(sw.channel)    # {'sw1': 3, 'sw2': 5}
```

---

### `sw.close()`

Parks both switches to CH6 and closes the serial port.

---

## Finding Your Serial Port

```python
import serial.tools.list_ports
for p in serial.tools.list_ports.comports():
    print(p.device, p.description)
```

On Linux, the Nano Every typically appears as `/dev/ttyACM0`.  
On Windows, check Device Manager for the `COMx` port.

---

## Error Handling

```python
from rf_switch import RFSwitch, RFSwitchError

with RFSwitch('COM3') as sw:
    try:
        sw.set(1, 3)
    except ValueError as e:
        print(f"Bad argument: {e}")
    except RFSwitchError as e:
        print(f"Switch error: {e}")
```

---

## License

MIT
