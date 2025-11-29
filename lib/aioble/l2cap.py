# MicroPython aioble module
# MIT license; Copyright (c) 2021 Jim Mussared

from micropython import const

import asyncio

from .core import ble, log_error, register_irq_handler
from .device import DeviceConnection


_IRQ_L2CAP_ACCEPT = const(22)
_IRQ_L2CAP_CONNECT = const(23)
_IRQ_L2CAP_DISCONNECT = const(24)
_IRQ_L2CAP_RECV = const(25)
_IRQ_L2CAP_SEND_READY = const(26)


# Once we start listening we're listening forever. (Limitation in NimBLE)
_listening = False


def _l2cap_irq(event, data):
    if event not in (
        _IRQ_L2CAP_CONNECT,
        _IRQ_L2CAP_DISCONNECT,
        _IRQ_L2CAP_RECV,
        _IRQ_L2CAP_SEND_READY,
    ):
        return

    # All the L2CAP events start with (conn_handle, cid, ...)
    if connection := DeviceConnection._connected.get(data[0], None):
        if channel := connection._l2cap_channel:
            # Expect to match the cid for this conn handle (unless we're
            # waiting for connection in which case channel._cid is None).
            if channel._cid is not None and channel._cid != data[1]:
                return

            # Update the channel object with new information.
            if event == _IRQ_L2CAP_CONNECT:
                _, channel._cid, _, channel.our_mtu, channel.peer_mtu = data
            elif event == _IRQ_L2CAP_DISCONNECT:
                _, _, psm, status = data
                channel._status = status
                channel._cid = None
                connection._l2cap_channel = None
            elif event == _IRQ_L2CAP_RECV:
                channel._data_ready = True
            elif event == _IRQ_L2CAP_SEND_READY:
                channel._stalled = False

            # Notify channel.
            channel._event.set()


def _l2cap_shutdown():
    global _listening
    _listening = False


r