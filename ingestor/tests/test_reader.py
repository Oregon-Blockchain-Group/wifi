import threading
from itertools import islice

import serial

from fake_firmware import BOOT_LOG, c5c6_line
from reader import MAX_LINE_BYTES, LineFramer, open_port, read_lines


class FakePort:
    """Serves scripted chunks from read(). An exception in the script is raised instead."""

    def __init__(self, script, stop=None):
        self.script = list(script)
        self.stop = stop
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.closed = True

    @property
    def in_waiting(self):
        return 0

    def read(self, size):
        if not self.script:
            if self.stop is not None:
                self.stop.set()
            return b""
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def opener_for(*results):
    """An opener that returns or raises each result in turn."""
    remaining = list(results)

    def opener(port, baudrate):
        result = remaining.pop(0)
        if isinstance(result, Exception):
            raise result
        return result
    return opener


def lines_from(stop, *results):
    return [line for line, _ in read_lines("fake", stop, retry_delay=0, opener=opener_for(*results))]


# LineFramer

def test_framer_splits_lines():
    assert LineFramer().feed(b"one\ntwo\n") == ["one", "two"]


def test_framer_joins_lines_split_across_chunks():
    framer = LineFramer()
    assert framer.feed(b"CSI_") == []
    assert framer.feed(b"DATA,1\nCSI") == ["CSI_DATA,1"]
    assert framer.feed(b"_DATA,2\n") == ["CSI_DATA,2"]


def test_framer_strips_carriage_returns():
    assert LineFramer().feed(b"one\r\n") == ["one"]


def test_framer_keeps_blank_lines():
    assert LineFramer().feed(b"one\n\ntwo\n") == ["one", "", "two"]


def test_framer_replaces_invalid_bytes():
    assert LineFramer().feed(b"CSI\xff\n") == ["CSI�"]


def test_framer_limits_a_line_with_no_newline():
    framer = LineFramer()
    junk = b"x" * (MAX_LINE_BYTES + 1)
    assert framer.feed(junk) == [junk.decode()]
    assert framer.feed(b"next\n") == ["next"]


# read_lines

def test_reads_lines_until_stopped():
    stop = threading.Event()
    port = FakePort([b"one\ntw", b"o\n"], stop)
    assert lines_from(stop, port) == ["one", "two"]
    assert port.closed


def test_lines_have_timezone_aware_timestamps():
    stop = threading.Event()
    results = list(read_lines("fake", stop, opener=opener_for(FakePort([b"one\n"], stop))))
    assert results[0][1].tzinfo is not None


def test_retries_until_port_appears():
    stop = threading.Event()
    missing = serial.SerialException("no such port")
    assert lines_from(stop, missing, missing, FakePort([b"one\n"], stop)) == ["one"]


def test_reconnects_and_drops_partial_line_after_disconnect():
    stop = threading.Event()
    first = FakePort([b"one\npartial", serial.SerialException("unplugged")])
    second = FakePort([b"two\n"], stop)
    assert lines_from(stop, first, second) == ["one", "two"]
    assert first.closed


def test_reads_firmware_output_through_real_pyserial():
    # loop:// is pyserial's in-memory port: whatever is written comes back from read()
    lines = [*BOOT_LOG, c5c6_line(seq=1), c5c6_line(seq=2)]
    port = open_port("loop://", 921600)
    assert port.dtr is False and port.rts is False
    port.write("".join(f"{line}\r\n" for line in lines).encode())

    reader = read_lines("loop://", threading.Event(), opener=lambda *_: port)
    assert [line for line, _ in islice(reader, len(lines))] == lines
    reader.close()
    assert not port.is_open
