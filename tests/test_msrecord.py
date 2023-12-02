import pytest
import os
import json
import math
import ctypes as ct
from mseedlib import MSRecord, DataEncoding

test_dir = os.path.abspath(os.path.dirname(__file__))
test_pack3 = os.path.join(test_dir, 'data', 'packtest_sine500.mseed3')
test_pack2 = os.path.join(test_dir, 'data', 'packtest_sine500.mseed2')

# A sine wave of 500 samples
sine_500 = list(map(lambda x: int(math.sin(math.radians(x)) * 500), range(0, 500)))

# A global record buffer
record_buffer = b''


def record_handler(record, handler_data):
    '''A callback function for MSRecord.set_record_handler()
    Stores the record in a global buffer for testing
    '''
    print("Record handler called, record length: %d" % len(record))
    global record_buffer
    record_buffer = bytes(record)


def test_msrecord_creation():

    # Test populating an MSRecord object with setters
    msr = MSRecord()
    msr.record_length = 512
    msr.sourceid = "FDSN:XX_TEST__B_S_X"
    msr.format_version = 3
    msr.flags = ct.c_uint8(0x04).value  # Set the 4th bit (clock locked) to 1
    msr.set_start_time_str("2023-01-02T01:02:03.123456789Z")
    msr.sample_rate = 50.0
    msr.encoding = DataEncoding.STEIM2  # value of 10
    msr.pub_version = 1
    msr.extra_headers = json.dumps({"FDSN": {"Time": {"Quality": 80}}})

    assert msr.record_length == 512
    assert msr.sourceid == "FDSN:XX_TEST__B_S_X"
    assert msr.format_version == 3
    assert msr.flags_dict() == {'clock_locked': True}
    assert msr.start_time == 1672621323123456789
    assert msr.start_time_seconds == 1672621323.1234567
    assert msr.sample_rate == 50.0
    assert msr.encoding == 11
    assert msr.pub_version == 1
    assert msr.extra_headers == '{"FDSN":{"Time":{"Quality":80}}}'

    # Test packing of an miniSEED v3 record
    msr.set_record_handler(record_handler, None)

    (packed_samples, packed_records) = msr.pack(data_samples=sine_500,
                                                sample_type='i',
                                                flush_data=True)

    assert packed_samples == 500
    assert packed_records == 1
    assert len(record_buffer) == 475

    with open(test_pack3, 'rb') as f:
        record_v3 = f.read()
        assert (record_buffer == record_v3)

    # Test packing of an miniSEED v2 record
    msr.format_version = 2

    (packed_samples, packed_records) = msr.pack(data_samples=sine_500,
                                                sample_type='i',
                                                flush_data=True)

    assert packed_samples == 500
    assert packed_records == 1
    assert len(record_buffer) == 512

    with open(test_pack2, 'rb') as f:
        record_v2 = f.read()
        assert (record_buffer == record_v2)
