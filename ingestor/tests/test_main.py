import queue
from datetime import datetime, timezone

from fake_firmware import BOOT_LOG, HEADER_C5C6, c5c6_line
from main import Stats, consume, ingest
from parser import DropReason

NOW = datetime(2026, 10, 29, 12, 0, tzinfo=timezone.utc)


def run_ingest(lines, maxsize=0):
    stats = Stats()
    records = queue.Queue(maxsize=maxsize)
    ingest(((line, NOW) for line in lines), stats, records)
    return stats, list(records.queue)


# Sequence tracking

def seq_stats(*seqs):
    stats = Stats()
    for seq in seqs:
        stats.observe_seq(seq)
    return stats


def test_consecutive_seqs_are_not_gaps():
    stats = seq_stats(5, 6, 7)
    assert (stats.seq_gaps, stats.seq_missed, stats.seq_resets) == (0, 0, 0)


def test_first_seq_is_not_a_gap():
    assert seq_stats(1000).seq_gaps == 0


def test_gaps_count_missing_packets():
    stats = seq_stats(1, 2, 5, 6, 8)
    assert (stats.seq_gaps, stats.seq_missed, stats.seq_resets) == (2, 3, 0)


def test_sender_reboot_is_a_reset_not_a_gap():
    stats = seq_stats(500, 501, 0, 1)
    assert (stats.seq_gaps, stats.seq_missed, stats.seq_resets) == (0, 0, 1)


def test_repeated_seq_is_a_reset():
    assert seq_stats(5, 5).seq_resets == 1


# ingest

def test_ingest_queues_records_and_counts_lines():
    stats, records = run_ingest([*BOOT_LOG, HEADER_C5C6, c5c6_line(seq=1), c5c6_line(seq=2)])
    assert [r.seq for r in records] == [1, 2]
    assert records[0].received_at == NOW
    assert stats.parsed == 2
    assert stats.other_lines == len(BOOT_LOG) + 1
    assert sum(stats.dropped.values()) == 0


def test_ingest_counts_each_drop_reason():
    line = c5c6_line(seq=1)
    stats, records = run_ingest([
        line[:-3],
        c5c6_line(csi=[1, 2], length=4),
        c5c6_line(rssi="x"),
        line + line,
        c5c6_line(seq=2),
    ])
    assert [r.seq for r in records] == [2]
    assert stats.dropped[DropReason.BAD_JSON] == 1
    assert stats.dropped[DropReason.LENGTH_MISMATCH] == 1
    assert stats.dropped[DropReason.BAD_FIELD] == 1
    assert stats.dropped[DropReason.COLUMN_COUNT] == 1


def test_dropped_lines_show_up_as_seq_gaps():
    stats, records = run_ingest([c5c6_line(seq=1), c5c6_line(seq=2)[:-3], c5c6_line(seq=3)])
    assert [r.seq for r in records] == [1, 3]
    assert stats.seq_missed == 1


def test_ingest_never_blocks_when_queue_is_full():
    stats, records = run_ingest([c5c6_line(seq=s) for s in range(5)], maxsize=2)
    assert [r.seq for r in records] == [0, 1]
    assert stats.parsed == 5
    assert stats.queue_full == 3


# consume

def queue_of(*items):
    q = queue.Queue()
    for item in items:
        q.put(item)
    return q


def test_consume_drains_queue_until_sentinel():
    received = []
    consume(queue_of("a", "b", None), received.append, Stats())
    assert received == ["a", "b"]


def test_consume_survives_sink_errors():
    received = []

    def sink(record):
        if record == "bad":
            raise RuntimeError("boom")
        received.append(record)

    stats = Stats()
    consume(queue_of("bad", "good", None), sink, stats)
    assert received == ["good"]
    assert stats.sink_errors == 1


def test_summary_lists_only_reasons_that_occurred():
    stats = Stats()
    stats.dropped[DropReason.BAD_JSON] = 2
    summary = stats.summary()
    assert "dropped=2" in summary
    assert "bad_json=2" in summary
    assert "bad_field" not in summary
