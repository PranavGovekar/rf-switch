"""
rf_switch.py
Python library for controlling two H6P-330127 SP6T RF switches
via an Arduino Nano Every running rf_switch_controller.ino.
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
    port      : Serial port, e.g. 'COM3' or '/dev/ttyACM0'
    baudrate  : Must match Arduino sketch (default 115200)
    timeout   : Serial read timeout in seconds (default 2)
    boot_wait : Seconds to wait for Arduino to boot (default 2)
    """

    def __init__(self, port: str, baudrate: int = 115200,
                 timeout: float = 2.0, boot_wait: float = 2.0):
        self._port = port
        self._ser  = serial.Serial(port, baudrate, timeout=timeout)
        self._sw1  = 6
        self._sw2  = 6
        time.sleep(boot_wait)
        self._ser.reset_input_buffer()

    def _send(self, cmd: str) -> str:
        if not self._ser.is_open:
            raise RFSwitchError("Serial port is closed.")
        self._ser.write((cmd.strip() + '\n').encode())
        response = self._ser.readline().decode().strip()
        if response.startswith('[ERR]'):
            raise RFSwitchError(f"Arduino error: {response}")
        return response

    @staticmethod
    def _validate(switch: int, channel: int):
        if switch not in (1, 2):
            raise ValueError(f"Switch must be 1 or 2, got {switch!r}")
        if channel not in range(1, 7):
            raise ValueError(f"Channel must be 1-6, got {channel!r}")

    def set(self, switch: int, channel: int) -> str:
        """
        Set a switch to a channel (one-hot encoding).

        Parameters
        ----------
        switch  : 1 or 2
        channel : 1 to 6

        Returns
        -------
        str : Response from Arduino, e.g. '[OK] SW1: CH3'

        Raises
        ------
        ValueError    : switch or channel out of range
        RFSwitchError : Arduino returned an error
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
        ch1 : Channel for Switch 1 (1-6)
        ch2 : Channel for Switch 2 (1-6)
        """
        self.set(1, ch1)
        self.set(2, ch2)

    def status(self) -> dict:
        """
        Query Arduino for current channel state.

        Returns
        -------
        dict : {'sw1': int, 'sw2': int}
        """
        resp = self._send("STATUS")
        result = {'sw1': self._sw1, 'sw2': self._sw2}
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
            pass
        return result

    @property
    def channel(self) -> dict:
        """
        Locally cached state — no serial round-trip.
        Use status() to confirm directly from the Arduino.

        Returns
        -------
        dict : {'sw1': int, 'sw2': int}
        """
        return {'sw1': self._sw1, 'sw2': self._sw2}

    def close(self):
        """Close the serial port. Switches hold their last set channel."""
        if self._ser.is_open:
            self._ser.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __repr__(self):
        return (f"RFSwitch(port={self._port!r}, "
                f"sw1=CH{self._sw1}, sw2=CH{self._sw2})")
