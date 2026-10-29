# A class defining a CSI record
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True)
class CsiRecord:
    received_at: datetime     # Pi wall-clock time when the line was read
    seq: int                  # sender's packet counter; gaps mean dropped packets
    mac: str                  # sender MAC address
    rssi: int                 # dBm
    noise_floor: int          # dBm
    channel: int
    local_timestamp: int      # ESP µs counter (32-bit, wraps every ~71 min)
    first_word_invalid: bool  # first 4 bytes of csi are invalid
    csi: list[int]            # [imag, real, imag, real, ...] per subcarrier
    fft_gain: int | None = None   # C5/C6 only
    agc_gain: int | None = None   # C5/C6 only
    extra: dict[str, int] = field(default_factory=dict)  # remaining esp-csi columns, stored as jsonb
