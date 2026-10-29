# Mimics the serial output of esp-csi's csi_recv example (examples/get-started/csi_recv/main/app_main.c)

HEADER_C5C6 = "type,seq,mac,rssi,rate,noise_floor,fft_gain,agc_gain,channel,local_timestamp,sig_len,rx_format,len,first_word,data"
HEADER_LEGACY = "type,id,mac,rssi,rate,sig_mode,mcs,bandwidth,smoothing,not_sounding,aggregation,stbc,fec_coding,sgi,noise_floor,ampdu_cnt,channel,secondary_channel,local_timestamp,ant,sig_len,rx_format,len,first_word,data"

BOOT_LOG = [
    "ESP-ROM:esp32c6-20220919",
    "I (283) main_task: Calling app_main()",
    "I (303) csi_recv: ================ CSI RECV ================",
]


def _i32(value: int) -> int:
    # Firmware prints uint32 fields with %d
    return value - 2**32 if value >= 2**31 else value


def _csi_suffix(csi: list[int], first_word_invalid: bool, length: int | None) -> str:
    n = len(csi) if length is None else length
    return f',{n},{int(first_word_invalid)},"[{",".join(str(v) for v in csi)}]"'


def c5c6_line(seq=7, mac="1a:00:00:00:00:00", rssi=-23, rate=11, noise_floor=-96, fft_gain=32,
              agc_gain=4, channel=11, timestamp=372852, sig_len=47, rx_format=0,
              csi=None, first_word_invalid=False, length=None) -> str:
    """A CSI_DATA line as printed by an ESP32-C5/C6/C61 receiver. Pass length to fake a mismatch."""
    csi = [0] * 256 if csi is None else csi
    return (f"CSI_DATA,{_i32(seq)},{mac},{rssi},{rate},{noise_floor},{fft_gain},{agc_gain},"
            f"{channel},{_i32(timestamp)},{sig_len},{rx_format}"
            + _csi_suffix(csi, first_word_invalid, length))


def legacy_line(seq=0, mac="94:d9:b3:80:8c:81", rssi=-30, rate=11, sig_mode=1, mcs=6, bandwidth=1,
                smoothing=0, not_sounding=1, aggregation=0, stbc=1, fec_coding=0, sgi=0,
                noise_floor=-93, ampdu_cnt=0, channel=13, secondary_channel=2, timestamp=2751923,
                ant=0, sig_len=67, csi=None, first_word_invalid=True, length=None) -> str:
    """A CSI_DATA line as printed by an ESP32/S2/S3/C3 receiver. Pass length to fake a mismatch."""
    csi = [0] * 128 if csi is None else csi
    # The firmware prints sig_mode again in the rx_state column
    return (f"CSI_DATA,{_i32(seq)},{mac},{rssi},{rate},{sig_mode},{mcs},{bandwidth},{smoothing},"
            f"{not_sounding},{aggregation},{stbc},{fec_coding},{sgi},{noise_floor},{ampdu_cnt},"
            f"{channel},{secondary_channel},{_i32(timestamp)},{ant},{sig_len},{sig_mode}"
            + _csi_suffix(csi, first_word_invalid, length))
