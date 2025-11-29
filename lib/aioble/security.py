# MicroPython aioble module
# MIT license; Copyright (c) 2021 Jim Mussared

from micropython import const, schedule
import asyncio
import binascii
import json

from .core import log_info, log_warn, ble, register_irq_handler
from .device import DeviceConnection

_IRQ_ENCRYPTION_UPDATE = const(28)
_IRQ_GET_SECRET = const(29)
_IRQ_SET_SECRET = const(30)
_IRQ_PASSKEY_ACTION = const(31)

_IO_CAPABILITY_DISPLAY_ONLY = const(0)
_IO_CAPABILITY_DISPLAY_YESNO = const(1)
_IO_CAPABILITY_KEYBOARD_ONLY = const(2)
_IO_CAPABILITY_NO_INPUT_OUTPUT = const(3)
_IO_CAPABILITY_KEYBOARD_DISPLAY = const(4)

_PASSKEY_ACTION_INPUT = const(2)
_PASSKEY_ACTION_DISP = const(3)
_PASSKEY_ACTION_NUMCMP = const(4)

_DEFAULT_PATH = "ble_secrets.json"

_secrets = {}
_modified = False
_path = None


# Must call this before stack startup.
def load_secrets(path=None):
    global _path, _secrets

    # Use path if specified, otherwise use previous path, otherwise use
    # default path.
    _path = path or _path or _DEFAULT_PATH

    # Reset old secrets.
    _secrets = {}
    try:
        with open(_path, "r") as f:
            entries = json.load(f)
            for sec_type, key, value in entries:
                # Decode bytes from hex.
                _secrets[sec_type, binascii.a2b_base64(key)] = binascii.a2b_base64(value)
    except:
        log_warn("No secrets available")


# Call this whenever the secrets dict changes.
def _save_secrets(arg=None):
    global _modified, _path

    _path = _path or _DEFAULT_PATH

    if not _modified:
        # Only save if the secrets changed.
        return

    with open(_path, "w") as f:
        # Convert bytes to hex strings (otherwise JSON will treat them like
        # strings).
        json_secrets = [
            (sec_type, binascii.b2a_base64(key), binascii.b2a_base64(value))
            for (sec_type, key), value in _secrets.items()
        ]
        json.dump(json_secrets, f)
        _modified = False


def _security_irq(event, data):
    global _modified

    if event == _IRQ_ENCRYPTION_UPDATE:
     