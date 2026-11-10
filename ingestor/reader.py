# Reads lines of text from the receiver ESP's serial port
import logging
import threading
from collections.abc import Callable, Iterator
from datetime import datetime, timezone

import serial

log = logging.getLogger(__name__)

DEFAULT_BAUD = 921600
READ_TIMEOUT_S = 0.2  # how often a quiet port checks whether it's time to stop
RETRY_DELAY_S = 2.0

# Far longer than any real line (384 CSI values is ~2 KB). Past this we're reading junk,
# for example at the wrong baud rate, and shouldn't keep buffering while we wait for a newline.
MAX_LINE_BYTES = 64 * 1024


class LineFramer:
    """Splits a stream of byte chunks into lines of text."""

    def __init__(self):
        self._partial = b""

    def feed(self, chunk: bytes) -> list[str]:
        *lines, self._partial = (self._partial + chunk).split(b"\n")
        if len(self._partial) > MAX_LINE_BYTES:
            # Passed on rather than discarded so that it gets counted downstream
            lines.append(self._partial)
            self._partial = b""
        # Corrupted bytes become U+FFFD, and the parser's checks then reject the line
        return [line.decode("utf-8", errors="replace").rstrip("\r") for line in lines]


def open_port(port: str, baudrate: int) -> serial.SerialBase:
    # Many ESP dev boards wire DTR/RTS to reset, so leave them low to avoid rebooting the
    # receiver just by connecting to it.
    ser = serial.serial_for_url(port, baudrate=baudrate, timeout=READ_TIMEOUT_S, do_not_open=True)
    ser.dtr = False
    ser.rts = False
    ser.open()
    return ser


def read_lines(
    port: str,
    stop: threading.Event,
    baudrate: int = DEFAULT_BAUD,
    retry_delay: float = RETRY_DELAY_S,
    opener: Callable[[str, int], serial.SerialBase] = open_port,
) -> Iterator[tuple[str, datetime]]:
    """Yield (line, received_at) from the serial port until stop is set.

    If the port is missing or drops out (USB unplugged, ESP resetting), keeps retrying until
    it comes back. Lines read from the same chunk share a received_at.
    """
    waiting = False  # so that a long outage logs once rather than on every retry
    while not stop.is_set():
        try:
            with opener(port, baudrate) as ser:
                log.info("connected to %s at %d baud", port, baudrate)
                waiting = False
                # A new framer per connection: a partial line from before a disconnect
                # can't be joined to whatever arrives after it.
                framer = LineFramer()
                while not stop.is_set():
                    # Take whatever is waiting. readline() would do a syscall per byte.
                    chunk = ser.read(max(1, ser.in_waiting))
                    if chunk:
                        received_at = datetime.now(timezone.utc)
                        for line in framer.feed(chunk):
                            yield line, received_at
        except OSError as e:  # includes serial.SerialException
            if not waiting:
                log.warning("serial port %s unavailable, retrying: %s", port, e)
                waiting = True
            stop.wait(retry_delay)
