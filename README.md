# rf-switch

Python library for controlling two **H6P-330127 SP6T RF switches** via an Arduino Nano Every.

---

## Installation

Install from GitHub:

```bash
pip install git+https://github.com/yourusername/rf-switch.git
```

**Requires:** Python 3.8+, `pyserial` (installed automatically)

---

## Hardware Setup

| Switch | Arduino Pins | Side |
|--------|-------------|------|
| SW1 | D2, D3, D4, D5, D6, D7 | Left |
| SW2 | A0, A1, A2, A3, A4, A5 | Right |

- Switch supply: **22–26V DC** (separate from Arduino)
- Logic: **TTL** — 3.3V output from Nano Every is compatible
- Arduino and switch must share a **common GND**

Flash the Arduino with `rf_switch_controller.ino` before using this library.

---

## Usage

```python
from rf_switch import RFSwitch

sw = RFSwitch('COM3')       # Windows — use '/dev/ttyACM0' on Linux

sw.set(1, 3)                # Switch 1 -> Channel 3
sw.set(2, 5)                # Switch 2 -> Channel 5
sw.set_both(2, 4)           # SW1 -> CH2, SW2 -> CH4

print(sw.status())          # {'sw1': 2, 'sw2': 4}  confirmed from Arduino
print(sw.channel)           # {'sw1': 2, 'sw2': 4}  cached, no serial call

sw.close()                  # Closes port; switches hold their last channel
```

### Context Manager

```python
from rf_switch import RFSwitch

with RFSwitch('COM3') as sw:
    sw.set(1, 1)
    sw.set(2, 6)
    print(sw.status())      # {'sw1': 1, 'sw2': 6}
# Port closes here; switches remain at SW1=CH1, SW2=CH6
```

---

## API Reference

### `RFSwitch(port, baudrate=115200, timeout=2.0, boot_wait=2.0)`

| Parameter | Default | Description |
|-----------|---------|-------------|
| `port` | — | e.g. `'COM3'` or `'/dev/ttyACM0'` |
| `baudrate` | `115200` | Must match the Arduino sketch |
| `timeout` | `2.0` | Serial read timeout (seconds) |
| `boot_wait` | `2.0` | Wait for Arduino boot on connect (seconds) |

---

### `sw.set(switch, channel) -> str`

Set a switch to a channel using one-hot encoding.

- `switch`: `1` or `2`
- `channel`: `1` to `6`

Raises `ValueError` for out-of-range arguments.  
Raises `RFSwitchError` if the Arduino returns an error.

---

### `sw.set_both(ch1, ch2)`

Set both switches in a single call. `ch1` → SW1, `ch2` → SW2.

---

### `sw.status() -> dict`

Ask the Arduino for the current state. Returns `{'sw1': int, 'sw2': int}`.

---

### `sw.channel -> dict`

Cached local state — no serial round-trip. Returns `{'sw1': int, 'sw2': int}`.

---

### `sw.close()`

Closes the serial port. Switches are **not changed** — they hold their last channel.

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

## Finding Your Serial Port

```python
import serial.tools.list_ports
for p in serial.tools.list_ports.comports():
    print(p.device, p.description)
```

On Linux the Nano Every typically appears as `/dev/ttyACM0`.

---

## License

MIT
