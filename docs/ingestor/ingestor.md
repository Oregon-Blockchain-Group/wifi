# Ingestor

## Purpose

The ingestor is the Python program that runs on the Raspberry Pi. It reads the serial output from the receiver ESP, picks out the CSI records, and uploads them to the cloud Postgres database. It covers steps 2 and 3 of the flow described in [Data Ingestion Layer](../wifi-data-ingestion.md).

It only moves raw data. It does not interpret CSI or try to infer anything about the room.

![Data collection and storage flow](../media/data_flow.png)

## Components

The code in `ingestor/` is split into three parts:

| File | Responsibility |
| --- | --- |
| `reader.py` | Opens the serial connection to the receiver ESP and yields lines of text. |
| `parser.py` | Picks out the CSI lines, validates them, and turns each one into a structured CSI record. |
| `uploader.py` | Batches parsed records and inserts them into Postgres. |

The parser should not depend on the serial port. It should take lines in and give records out, so it can be tested against saved captures without the hardware plugged in.

## Receiver Output

We're using the `csi_send` and `csi_recv` firmware from Espressif's [esp-csi](https://github.com/espressif/esp-csi) `examples/get-started`. The sender broadcasts small ESP-NOW packets (100 per second by default), each containing an incrementing counter. The receiver computes CSI for every packet it gets from the sender and prints one line of text to serial for each one. The serial connection runs at 921600 baud.

The output is plain text, not binary. Each CSI record is one CSV line starting with `CSI_DATA`, and the CSI values are a quoted, JSON-style array at the end:

```
CSI_DATA,7,1a:00:00:00:00:00,-23,11,-96,32,4,11,372852,47,0,256,0,"[0,0,0,0,-6,-13,-6,-14,...]"
```

The receiver also prints other lines on the same port: boot messages, ESP-IDF log lines, and a header line with the column names when the first packet arrives. The ingestor has to skip anything that doesn't start with `CSI_DATA`.

### Columns

The columns depend on which chip the receiver is.

**ESP32-C5 / C6 / C61** (15 columns):

```
type,seq,mac,rssi,rate,noise_floor,fft_gain,agc_gain,channel,local_timestamp,sig_len,rx_state,len,first_word,data
```

**Older chips: ESP32, S2, S3, C3** (25 columns):

```
type,id,mac,rssi,rate,sig_mode,mcs,bandwidth,smoothing,not_sounding,aggregation,stbc,fec_coding,sgi,noise_floor,ampdu_cnt,channel,secondary_channel,local_timestamp,ant,sig_len,rx_state,len,first_word,data
```

The fields that matter most to us:

| Field | Description |
| --- | --- |
| `type` | Always `CSI_DATA` |
| `seq` / `id` | The sender's packet counter, so gaps mean dropped packets |
| `mac` | Sender MAC address (the example sender uses `1a:00:00:00:00:00`) |
| `rssi` | Signal strength (dBm) |
| `noise_floor` | Noise floor (dBm) |
| `channel` | Wi-Fi channel (the examples default to 11) |
| `local_timestamp` | Receiver time when the packet arrived, in µs. It's a 32-bit counter, so it wraps around about every 71.6 minutes and resets when the ESP reboots. |
| `fft_gain`, `agc_gain` | Receiver gain settings (C5/C6 only). Useful for normalizing amplitude later. |
| `len` | Number of values in `data` |
| `first_word` | 1 if the first four bytes of `data` are invalid |
| `data` | The CSI values |

### CSI Values

`data` is a list of signed integers. Each subcarrier takes two values, with the imaginary part first: `[imag₁, real₁, imag₂, real₂, ...]`. So the number of subcarriers is `len / 2`.

`len` is not fixed. It depends on the chip, the bandwidth (20 or 40 MHz) and which training fields the firmware is set to capture (LLTF, HT-LTF, STBC-HT-LTF). Espressif's examples show lengths of 128, 256 and 384, among others. Some values are always zero, such as the guard subcarriers at the edges of the band and the null subcarrier in the middle. The ingestor should store the array as-is and leave cleanup to later processing.

## Parsing

For each line from the serial port, the parser:

1. Skips the line if it doesn't start with `CSI_DATA`. Optionally, logs it for debugging.
2. Splits it as CSV. Python's `csv` module handles the quoted `data` field.
3. Checks the column count is 15 or 25 and maps the columns to field names. If the count doesn't match, the line was garbled or cut off, so it's dropped.
4. Parses `data` as a JSON array. If parsing fails, the line was cut off and is dropped.
5. Checks that the array has exactly `len` values. If not, the line is dropped.

Espressif's own `tools/csi_data_read_parse.py` does the same checks, and is a useful reference.

There is no checksum, so these checks are the only protection against corrupted lines. Espressif notes that lines get garbled when the reading side falls behind and the serial buffer overflows. That's another reason to keep the reader loop doing as little as possible and do the uploads off the reader thread.

## Data Volume

Text takes more space than the binary estimate in the data ingestion doc. A line with 128 CSI values is roughly 450–600 bytes, and at the sender's default of 100 packets per second that's about 50–60 KB/s over serial. The link at 921600 baud carries about 92 KB/s, so there's headroom for 128 values but not much for 384. If longer CSI arrays or higher packet rates are needed, lower the send frequency or raise the baud rate.

The text format only applies on the serial link. Once parsed, a record with 128 CSI values packed as 1-byte integers is close to the 152 bytes per record estimated in the data ingestion doc. Note that the sender default is 100 packets/second, double the 50 used in that estimate.

## Upload

At 100 records per second, uploading one row at a time would mean 100 round trips per second to the cloud database. Instead, the uploader should:

- Collect records into batches, flushing either every N records or every few seconds, whichever comes first.
- Insert each batch in a single statement.
- Hold failed batches in memory (or on local disk) and retry them, so a dropped connection doesn't lose data.

Each record maps to one row, with one column per metadata field. The CSI array can be stored as a `smallint[]` column, or packed into `bytea` to save space.

## Error Handling and Monitoring

The ingestor should keep counts it can log periodically:

- Records parsed
- Lines dropped as garbled, and which check they failed
- Gaps in `seq`, which indicate packets the receiver never got
- Upload failures and retries

This doesn't solve missing or corrupted data, but it makes it visible, which the later processing work will need.

## Open Questions

- **Chip:** which ESP chip are we using for the receiver? That decides which column set we get. Espressif recommends the C5 or C6 and an external antenna.
- **Firmware changes:** do we run the esp-csi examples unmodified, or change them? For example, we could switch to a compact binary output if serial bandwidth becomes a problem.
- **CSI configuration:** which training fields and bandwidth should we capture? This determines `len`.
- **Gain control:** the receiver example can lock the receiver gain (`CONFIG_GAIN_CONTROL` / `CONFIG_FORCE_GAIN`) so amplitudes are comparable over time. Should we enable it?
- **Session tracking:** should rows carry a session or device ID so separate recording runs can be told apart?
- **Timestamps:** since `local_timestamp` wraps around and resets, should the ingestor also store the Pi's wall-clock time when it reads each line?
- **Schema:** the final column list depends on Kevin's architecture plan.
