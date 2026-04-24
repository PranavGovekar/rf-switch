"""
rf_switch.py
============
Python library for controlling two H6P-330127 SP6T RF switches
via an Arduino Nano Every running rf_switch_controller.ino.

Install dependency:
    pip install pyserial

Usage:
    from rf_switch import RFSwitch

    sw = RFSwitch('COM3')          # or '/dev/ttyACM0' on Linux
    sw.set(1, 3)                   # Switch 1 -> Channel 3
    sw.set(2, 5)                   # Switch 2 -> Channel 5
    sw.status()                    # {'sw1': 3, 'sw2': 5}
    sw.default()                   # Both switches -> CH6
    sw.close()

    # Or use as a context manager (auto-closes safely):
    with RFSwitch('COM3') as sw:
        sw.set(1, 2)
        sw.set(2, 4)
"""

import serial
import time


class RFSwitchError(Exception):
    """Raised when the Arduino returns an error response."""
    pass


class RFSwitch:
    """
    Controls two H6P-330127 SP6T RF switches via serial.

    Parameters
    ----------
    port     : Serial port string, e.g. 'COM3' or '/dev/ttyACM0'
    baudrate : Must match Arduino sketch (default 115200)
    timeout  : Serial read timeout in seconds (default 2)
    boot_wait: Seconds to wait for Arduino to boot after connecting (default 2)
    """

    VALID_SWITCHES  = (1, 2)
    VALID_CHANNELS  = range(1, 7)   # 1–6

    def __init__(self, port: str, baudrate: int = 115200,
                 timeout: float = 2.0, boot_wait: float = 2.0):
        self._port = port
        self._ser  = serial.Serial(port, baudrate, timeout=timeout)
        self._sw1  = 6   # Mirrors Arduino default (CH6 on boot)
        self._sw2  = 6
        time.sleep(boot_wait)
        self._flush()

    # ── Private Helpers ───────────────────────────────────────────────────────

    def _flush(self):
        """Discard any pending bytes (e.g. boot messages)."""
        self._ser.reset_input_buffer()

    def _send(self, cmd: str) -> str:
        """Send a command string, return the response line."""
        if not self._ser.is_open:
            raise RFSwitchError("Serial port is closed.")
        self._ser.write((cmd.strip() + '\n').encode())
        response = self._ser.readline().decode().strip()
        if response.startswith('[ERR]'):
            raise RFSwitchError(f"Arduino error: {response}")
        return response

    @staticmethod
    def _validate(switch: int, channel: int):
        if switch not in RFSwitch.VALID_SWITCHES:
            raise ValueError(f"Switch must be 1 or 2, got {switch!r}")
        if channel not in RFSwitch.VALID_CHANNELS:
            raise ValueError(f"Channel must be 1–6, got {channel!r}")

    # ── Public API ────────────────────────────────────────────────────────────

    def set(self, switch: int, channel: int) -> str:
        """
        Set a switch to a channel using one-hot encoding.

        Parameters
        ----------
        switch  : 1 or 2
        channel : 1 to 6

        Returns
        -------
        str : Raw response from Arduino, e.g. '[OK] SW1: CH3'

        Raises
        ------
        ValueError      : If switch or channel is out of range
        RFSwitchError   : If Arduino returns an error
        """
        self._validate(switch, channel)
        resp = self._send(f"S{switch}C{channel}")
        if switch == 1:
            self._sw1 = channel
        else:
            self._sw2 = channel
        return resp

    def set_both(self, ch1: int, ch2: int):
        """
        Set both switches in one call.

        Parameters
        ----------
        ch1 : Channel for Switch 1 (1–6)
        ch2 : Channel for Switch 2 (1–6)
        """
        self.set(1, ch1)
        self.set(2, ch2)

    def default(self, switch: int = None) -> str:
        """
        Park switch(es) to CH6 (safe hardware default for H6P-330127).

        Parameters
        ----------
        switch : 1, 2, or None (None = both switches)
        """
        if switch == 1:
            return self.set(1, 6)
        elif switch == 2:
            return self.set(2, 6)
        else:
            self.set(1, 6)
            return self.set(2, 6)

    def status(self) -> dict:
        """
        Query the Arduino for current channel state.

        Returns
        -------
        dict : {'sw1': int_or_None, 'sw2': int_or_None}
               Channel is None if the switch is in an undefined state.
        """
        resp = self._send("STATUS")
        # Parse response: '[STATUS] SW1=3  SW2=5'
        result = {'sw1': None, 'sw2': None}
        try:
            parts = resp.replace('[STATUS]', '').split()
            for part in parts:
                key, val = part.split('=')
                ch = None if val == 'OFF' else int(val)
                if key == 'SW1':
                    result['sw1'] = ch
                    self._sw1 = ch
                elif key == 'SW2':
                    result['sw2'] = ch
                    self._sw2 = ch
        except Exception:
            pass  # Return partial result if parsing fails
        return result

    @property
    def channel(self) -> dict:
        """
        Cached local state (no serial round-trip).
        Use status() if you need to confirm from the Arduino.

        Returns
        -------
        dict : {'sw1': int, 'sw2': int}
        """
        return {'sw1': self._sw1, 'sw2': self._sw2}

    def close(self):
        """Park both switches to CH6 and close the serial port."""
        try:
            self.default()
        except Exception:
            pass
        if self._ser.is_open:
            self._ser.close()

    # ── Context Manager ───────────────────────────────────────────────────────

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __repr__(self):
        return (f"RFSwitch(port={self._port!r}, "
                f"sw1=CH{self._sw1}, sw2=CH{self._sw2})")
