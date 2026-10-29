from datetime import datetime, timezone
from pathlib import Path

import pytest

from fake_firmware import BOOT_LOG, HEADER_C5C6, HEADER_LEGACY, c5c6_line, legacy_line
from parser import parse_line

DATA = Path(__file__).parent / "data"
NOW = datetime(2026, 10, 29, 12, 0, tzinfo=timezone.utc)


def parse(line):
    return parse_line(line, NOW)


# Real example lines from the esp-csi get-started README

def test_readme_c5c6_line():
    record = parse((DATA / "esp_csi_c5c6.txt").read_text().strip())
    assert record is not None
    assert record.received_at == NOW
    assert record.seq == 7
    assert record.mac == "1a:00:00:00:00:00"
    assert record.rssi == -23
    assert record.noise_floor == -96
    assert record.channel == 11
    assert record.local_timestamp == 372852
    assert record.first_word_invalid is False
    assert record.fft_gain == 32
    assert record.agc_gain == 4
    assert len(record.csi) == 256
    assert record.csi[12:14] == [-6, -13]
    assert record.extra == {"rate": 11, "sig_len": 47, "rx_state": 0}


def test_readme_legacy_line():
    record = parse((DATA / "esp_csi_legacy.txt").read_text().strip())
    assert record is not None
    assert record.seq == 0
    assert record.mac == "94:d9:b3:80:8c:81"
    assert record.rssi == -30
    assert record.noise_floor == -93
    assert record.channel == 13
    assert record.local_timestamp == 2751923
    assert record.first_word_invalid is True
    assert record.fft_gain is None
    assert record.agc_gain is None
    assert len(record.csi) == 128
    assert record.csi[:4] == [67, 48, 4, 0]
    assert record.extra["bandwidth"] == 1
    assert record.extra["secondary_channel"] == 2
    assert set(record.extra) == {
        "rate", "sig_mode", "mcs", "bandwidth", "smoothing", "not_sounding", "aggregation",
        "stbc", "fec_coding", "sgi", "ampdu_cnt", "secondary_channel", "ant", "sig_len", "rx_state",
    }


# Lines that aren't CSI records

@pytest.mark.parametrize("line", [*BOOT_LOG, HEADER_C5C6, HEADER_LEGACY, ""])
def test_non_csi_lines_are_skipped(line):
    assert parse(line) is None


def test_stream_keeps_only_csi_lines():
    lines = [*BOOT_LOG, HEADER_C5C6, c5c6_line(seq=1), "W (5000) wifi: something", c5c6_line(seq=2)]
    records = [r for r in map(parse, lines) if r is not None]
    assert [r.seq for r in records] == [1, 2]


# Malformed records

@pytest.mark.parametrize("line", [c5c6_line(), legacy_line()])
def test_truncated_lines_are_rejected(line):
    for cut in (len(line) // 3, len(line) // 2, len(line) - 3):
        assert parse(line[:cut]) is None


def test_length_mismatch_is_rejected():
    assert parse(c5c6_line(csi=[1, 2, 3, 4], length=6)) is None


def test_wrong_column_count_is_rejected():
    line = c5c6_line()
    assert parse(line.replace("CSI_DATA,", "CSI_DATA,99,", 1)) is None


def test_non_numeric_field_is_rejected():
    assert parse(c5c6_line(rssi="x")) is None


def test_non_integer_csi_is_rejected():
    line = c5c6_line(csi=[1, 2]).replace("[1,2]", "[1,2.5]")
    assert parse(line) is None


def test_two_lines_run_together_are_rejected():
    # Happens when a newline is lost and the next line is appended
    assert parse(c5c6_line(seq=1) + c5c6_line(seq=2)) is None


# Counter wraparound

def test_timestamp_past_2_31_is_unsigned():
    # The firmware prints the uint32 timestamp with %d, so after ~35.8 min it comes out negative
    ts = 2**31 + 1000
    line = c5c6_line(timestamp=ts)
    assert f",{ts - 2**32}," in line
    assert parse(line).local_timestamp == ts


def test_seq_past_2_31_is_unsigned():
    assert parse(c5c6_line(seq=2**32 - 1)).seq == 2**32 - 1


def test_csi_values_round_trip():
    csi = [(-1) ** i * (i % 128) for i in range(256)]
    assert parse(c5c6_line(csi=csi)).csi == csi
