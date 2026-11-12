# Entry point: wires the serial reader and parser to a sink, and logs stats as it runs
import argparse
import logging
import queue
import signal
import threading
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import datetime

from parser import DropReason, MalformedLine, parse_line
from reader import DEFAULT_BAUD, read_lines
from record import CsiRecord

log = logging.getLogger("ingestor")

# Records waiting for the sink: 60 seconds' worth at the sender's default 100 per second
QUEUE_SIZE = 6000
STATS_INTERVAL_S = 10.0


@dataclass
class Stats:
    parsed: int = 0
    other_lines: int = 0  # boot messages, logs and the header
    # Every reason is present from the start, so the dict never resizes while being logged
    dropped: dict[DropReason, int] = field(default_factory=lambda: dict.fromkeys(DropReason, 0))
    seq_gaps: int = 0        # number of times seq jumped forward
    seq_missed: int = 0      # packets the receiver never got, summed across those jumps
    seq_resets: int = 0      # seq repeated or went backwards, which usually means the sender rebooted
    queue_full: int = 0      # records lost because the sink had fallen too far behind
    sink_errors: int = 0
    _last_seq: int | None = None

    def observe_seq(self, seq: int) -> None:
        last, self._last_seq = self._last_seq, seq
        if last is None or seq == last + 1:
            return
        if seq > last:
            self.seq_gaps += 1
            self.seq_missed += seq - last - 1
        else:
            self.seq_resets += 1

    def summary(self) -> str:
        reasons = "".join(f" {reason.value}={n}" for reason, n in self.dropped.items() if n)
        return (
            f"parsed={self.parsed} other_lines={self.other_lines} "
            f"dropped={sum(self.dropped.values())}{reasons} "
            f"seq_gaps={self.seq_gaps} seq_missed={self.seq_missed} seq_resets={self.seq_resets} "
            f"queue_full={self.queue_full} sink_errors={self.sink_errors}"
        )


def ingest(
    lines: Iterable[tuple[str, datetime]],
    stats: Stats,
    records: "queue.Queue[CsiRecord | None]",
) -> None:
    """Parse lines onto the queue. Never blocks on the queue, so a slow sink can't stall the
    serial read and overflow the port's buffer."""
    for line, received_at in lines:
        try:
            record = parse_line(line, received_at)
        except MalformedLine as e:
            stats.dropped[e.reason] += 1
            log.debug("dropped (%s): %s", e.reason.value, line)
            continue
        if record is None:
            stats.other_lines += 1
            log.debug("serial: %s", line)
            continue
        stats.parsed += 1
        stats.observe_seq(record.seq)
        try:
            records.put_nowait(record)
        except queue.Full:
            stats.queue_full += 1


def consume(
    records: "queue.Queue[CsiRecord | None]",
    sink: Callable[[CsiRecord], None],
    stats: Stats,
) -> None:
    """Pass records to the sink until a None arrives on the queue."""
    while (record := records.get()) is not None:
        try:
            sink(record)
        except Exception:
            stats.sink_errors += 1
            log.exception("sink failed, record lost")


def discard(record: CsiRecord) -> None:
    """Placeholder sink until uploader.py exists."""


def run(port: str, baudrate: int, stats_interval: float, sink: Callable[[CsiRecord], None] = discard) -> int:
    stats = Stats()
    stop = threading.Event()
    records: queue.Queue[CsiRecord | None] = queue.Queue(maxsize=QUEUE_SIZE)
    crashed = threading.Event()

    def read_and_parse() -> None:
        try:
            ingest(read_lines(port, stop, baudrate=baudrate), stats, records)
        except Exception:
            log.exception("reader thread crashed")
            crashed.set()
        finally:
            stop.set()  # wake the main thread so the process exits instead of idling

    for signum in (signal.SIGINT, signal.SIGTERM):
        signal.signal(signum, lambda *_: stop.set())

    reader_thread = threading.Thread(target=read_and_parse, name="reader")
    sink_thread = threading.Thread(target=consume, args=(records, sink, stats), name="sink")
    reader_thread.start()
    sink_thread.start()

    # Logging from here, not the reader thread, keeps stats coming while the port is down
    while not stop.wait(stats_interval):
        log.info("%s queue_depth=%d", stats.summary(), records.qsize())

    reader_thread.join()
    records.put(None)  # the sink thread drains everything queued ahead of this, then exits
    sink_thread.join()
    log.info("final: %s", stats.summary())
    return 1 if crashed.is_set() else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Read CSI records from a receiver ESP's serial port.")
    parser.add_argument("port", help="serial port, e.g. /dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD, help="default: %(default)s")
    parser.add_argument("--stats-interval", type=float, default=STATS_INTERVAL_S,
                        help="seconds between stats log lines, default: %(default)s")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="also log every non-CSI and dropped line")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    return run(args.port, args.baud, args.stats_interval)


if __name__ == "__main__":
    raise SystemExit(main())
