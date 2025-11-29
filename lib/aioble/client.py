# MicroPython aioble module
# MIT license; Copyright (c) 2021 Jim Mussared

from micropython import const
from collections import deque
import asyncio
import struct

import bluetooth

from .core import ble, GattError, register_irq_handler
from .device import DeviceConnection


_IRQ_GATTC_SERVICE_RESULT = const(9)
_IRQ_GATTC_SERVICE_DONE = const(10)
_IRQ_GATTC_CHARACTERISTIC_RESULT = const(11)
_IRQ_GATTC_CHARACTERISTIC_DONE = const(12)
_IRQ_GATTC_DESCRIPTOR_RESULT = const(13)
_IRQ_GATTC_DESCRIPTOR_DONE = const(14)
_IRQ_GATTC_READ_RESULT = const(15)
_IRQ_GATTC_READ_DONE = const(16)
_IRQ_GATTC_WRITE_DONE = const(17)
_IRQ_GATTC_NOTIFY = const(18)
_IRQ_GATTC_INDICATE = const(19)

_CCCD_UUID = const(0x2902)
_CCCD_NOTIFY = const(1)
_CCCD_INDICATE = const(2)

_FLAG_READ = const(0x0002)
_FLAG_WRITE_NO_RESPONSE = const(0x0004)
_FLAG_WRITE = const(0x0008)
_FLAG_NOTIFY = const(0x0010)
_FLAG_INDICATE = const(0x0020)


# Forward IRQs directly to static methods on the type that handles them and
# knows how to map handles to instances. Note: We copy all uuid and data
# params here for safety, but a future optimisation might be able to avoid
# these copies in a few places.
def _client_irq(event, data):
    if event == _IRQ_GATTC_SERVICE_RESULT:
        conn_handle, start_handle, end_handle, uuid = data
        ClientDiscover._discover_result(
            conn_handle, start_handle, end_handle, bluetooth.UUID(uuid)
        )
    elif event == _IRQ_GATTC_SERVICE_DONE:
        conn_handle, status = data
        ClientDiscover._discover_done(conn_handle, status)
    elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT:
        conn_handle, end_handle, value_handle, properties, uuid = data
        ClientDiscover._discover_result(
            conn_handle, end_handle, value_handle, properties, bluetooth.UUID(uuid)
        )
    elif event == _IRQ_GATTC_CHARACTERISTIC_DONE:
        conn_handle, status = data
        ClientDiscover._discover_done(conn_handle, status)
    elif event == _IRQ_GATTC_DESCRIPTOR_RESULT:
        conn_handle, dsc_handle, uuid = data
        ClientDiscover._discover_result(conn_handle, dsc_handle, bluetooth.UUID(uuid))
    elif event == _IRQ_GATTC_DESCRIPTOR_DONE:
        conn_handle, status = data
        ClientDiscover._discover_done(conn_handle, status)
    elif event 