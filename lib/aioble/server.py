# MicroPython aioble module
# MIT license; Copyright (c) 2021 Jim Mussared

from micropython import const
from collections import deque
import bluetooth
import asyncio

from .core import (
    ensure_active,
    ble,
    log_info,
    log_error,
    log_warn,
    register_irq_handler,
    GattError,
)
from .device import DeviceConnection, DeviceTimeout

_registered_characteristics = {}

_IRQ_GATTS_WRITE = const(3)
_IRQ_GATTS_READ_REQUEST = const(4)
_IRQ_GATTS_INDICATE_DONE = const(20)

_FLAG_READ = const(0x0002)
_FLAG_WRITE_NO_RESPONSE = const(0x0004)
_FLAG_WRITE = const(0x0008)
_FLAG_NOTIFY = const(0x0010)
_FLAG_INDICATE = const(0x0020)

_FLAG_READ_ENCRYPTED = const(0x0200)
_FLAG_READ_AUTHENTICATED = const(0x0400)
_FLAG_READ_AUTHORIZED = const(0x0800)
_FLAG_WRITE_ENCRYPTED = const(0x1000)
_FLAG_WRITE_AUTHENTICATED = const(0x2000)
_FLAG_WRITE_AUTHORIZED = const(0x4000)

_FLAG_WRITE_CAPTURE = const(0x10000)


_WRITE_CAPTURE_QUEUE_LIMIT = const(10)


def _server_irq(event, data):
    if event == _IRQ_GATTS_WRITE:
        conn_handle, attr_handle = data
        Characteristic._remote_write(conn_handle, attr_handle)
    elif event == _IRQ_GATTS_READ_REQUEST:
        conn_handle, attr_handle = data
        return Characteristic._remote_read(conn_handle, attr_handle)
    elif event == _IRQ_GATTS_INDICATE_DONE:
        conn_handle, value_handle, status = data
        Characteristic._indicate_done(conn_handle, value_handle, status)


def _server_shutdown():
    global _registered_characteristics
    _registered_characteristics = {}
    if hasattr(BaseCharacteristic, "_capture_task"):
        BaseCharacteristic._capture_task.cancel()
        del BaseCharacteristic._capture_queue
        del BaseCharacteristic._capture_write_event
        del BaseCharacteristic._capture_consumed_event
        del BaseCharacteristic._capture_task


register_irq_handler(_server_irq, _server_shutdown)


class Service:
    def __init__(self, uuid):
        self.uuid = uuid
        self.characteristics = []

    # Generate tuple for gatts_register_services.
    def _tuple(self):
        return (self.uuid, t