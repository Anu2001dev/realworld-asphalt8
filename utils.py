import asyncio
import functools
import glob
import os
import sys
from typing import Callable

import pyfirmata
import serial
from rich.console import Console
from serial.tools import list_ports

console = Console(highlight=False)


class NoValidPortError(Exception):
    pass


class BoardNotPluggedError(Exception):
    pass


def colorize(text: str, color: str) -> str:
    return f"[{color}]{text}[/{color}]"


def forever(*, delay: float):
    def wrapper(coro: Callable):
        @functools.wraps(coro)
        async def wrapped(*args, **kwargs):
            while True:
                await coro(*args, **kwargs)
                await asyncio.sleep(delay)

        return wrapped

    return wrapper


def get_color(text: bool):
    color = "green" if text else "red"
    return colorize(str(text), color)


def get_port():
    if sys.platform == "linux":
        try:
            (port,) = glob.glob("/dev/ttyUSB*")
        except ValueError:
            raise BoardNotPluggedError
    elif sys.platform == "win32":
        comports = list_ports.comports()
        (port, *_) = (port[0] for port in comports if "USB-SERIAL" in port[1])
    else:
        # set an environment variable for port or set port manually
        port = os.environ.get("PORT")

    return port


def exit_program():
    console.log("[bold cyan]Exiting...")
    exit()


port = get_port()


class ArduinoNano(pyfirmata.Board):
    def __init__(self, port=port, *args, **kwargs):
        layout = {
            "digital": (1, 0, *range(2, 14)),
            "analog": tuple(range(8)),
            "pwm": (3, 5, 6, 9, 10, 11),
            "use_ports": True,
            "disabled": (0, 1),
        }
        try:
            super().__init__(layout=layout, port=port, *args, **kwargs)

        except serial.SerialException:
            exit_program()

        it = pyfirmata.util.Iterator(self)
        it.start()
