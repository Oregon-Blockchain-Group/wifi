# Turns lines of esp-csi serial output into CSI records
import csv
import json
from datetime import datetime
from enum import Enum

from record import CsiRecord

# Column order printed by esp-csi's csi_recv example, per chip family.
# The legacy format calls the sequence column "id"; we name it "seq" in both.
COLUMNS_C5C6 = [
    "type", "seq", "mac", "rssi", "rate", "noise_floor", "fft_gain", "agc_gain",
    "channel", "local_timestamp", "sig_len", "rx_format", "len", "first_word", "data",
]
COLUMNS_LEGACY = [
    "type", "seq", "mac", "rssi", "rate", "sig_mode", "mcs", "bandwidth", "smoothing",
    "not_sounding", "aggregation", "stbc", "fec_coding", "sgi", "noise_floor", "ampdu_cnt",
    "channel", "secondary_channel", "local_timestamp", "ant", "sig_len", "rx_format",
    "len", "first_word", "data",
]
FORMATS = {len(COLUMNS_C5C6): COLUMNS_C5C6, len(COLUMNS_LEGACY): COLUMNS_LEGACY}

# Columns that map to typed CsiRecord fields; everything else goes in extra
TYPED = {
    "type", "seq", "mac", "rssi", "noise_floor", "channel", "local_timestamp",
    "first_word", "data", "len", "fft_gain", "agc_gain",
}


class DropReason(Enum):
    """Which check a CSI_DATA line failed."""
    BAD_CSV = "bad_csv"
    COLUMN_COUNT = "column_count"          # garbled, or two lines run together
    BAD_JSON = "bad_json"                  # usually a line cut off inside the data array
    BAD_CSI = "bad_csi"                    # valid JSON, but not a list of integers
    LENGTH_MISMATCH = "length_mismatch"    # array size doesn't match the len column
    BAD_FIELD = "bad_field"                # non-numeric metadata


class MalformedLine(Exception):
    """A line claimed to be a CSI record but failed validation."""

    def __init__(self, reason: DropReason):
        super().__init__(reason.value)
        self.reason = reason


def _u32(value: str) -> int:
    # The firmware prints unsigned 32-bit counters with %d, so they go negative past 2^31
    return int(value) % 2**32


def parse_line(line: str, received_at: datetime) -> CsiRecord | None:
    """Parse one line of serial output.

    Returns None for lines that aren't CSI records (boot messages, logs, the header).
    Raises MalformedLine for CSI_DATA lines that fail validation.
    """
    if not line.startswith("CSI_DATA,"):
        return None

    try:
        values = next(csv.reader([line]))
    except csv.Error:
        raise MalformedLine(DropReason.BAD_CSV) from None
    columns = FORMATS.get(len(values))
    if columns is None:
        raise MalformedLine(DropReason.COLUMN_COUNT)
    row = dict(zip(columns, values))

    try:
        csi = json.loads(row["data"])
    except ValueError:
        raise MalformedLine(DropReason.BAD_JSON) from None
    if not isinstance(csi, list) or not all(type(v) is int for v in csi):
        raise MalformedLine(DropReason.BAD_CSI)

    try:
        length = int(row["len"])
        record = CsiRecord(
            received_at=received_at,
            seq=_u32(row["seq"]),
            mac=row["mac"],
            rssi=int(row["rssi"]),
            noise_floor=int(row["noise_floor"]),
            channel=int(row["channel"]),
            local_timestamp=_u32(row["local_timestamp"]),
            first_word_invalid=bool(int(row["first_word"])),
            csi=csi,
            fft_gain=int(row["fft_gain"]) if "fft_gain" in row else None,
            agc_gain=int(row["agc_gain"]) if "agc_gain" in row else None,
            extra={k: int(v) for k, v in row.items() if k not in TYPED},
        )
    except ValueError:
        raise MalformedLine(DropReason.BAD_FIELD) from None
    if len(csi) != length:
        raise MalformedLine(DropReason.LENGTH_MISMATCH)
    return record
