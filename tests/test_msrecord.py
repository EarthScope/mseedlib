import pytest
import os
import json
import math
import ctypes as ct
from mseedlib import MS3Record, DataEncoding

test_dir = os.path.abspath(os.path.dirname(__file__))
test_pack3 = os.path.join(test_dir, 'data', 'packtest_sine500.mseed3')
test_pack2 = os.path.join(test_dir, 'data', 'packtest_sine500.mseed2')

# A sine wave of 500 samples
sine_500 = list(map(lambda x: int(math.sin(math.radians(x)) * 500), range(0, 500)))

# A global record buffer
record_buffer = b''


def record_handler(record, handler_data):
    '''A callback function for MS3Record.set_record_handler()
    Stores the record in a global buffer for testing
    '''
    print("Record handler called, record length: %d" % len(record))
    global record_buffer
    record_buffer = bytes(record)

class TestMS3RecordSorting:
    def test_same_time_different_subsource(self):
        msr1 = MS3Record()
        msr1.set_starttime_str("2023-01-02T01:02:03.123456789Z")
        msr1.sourceid = "FDSN:XX_TEST__B_S_X"

        msr2 = MS3Record()
        msr2.set_starttime_str("2023-01-02T01:02:03.123456789Z")
        msr2.sourceid = "FDSN:XX_TEST__B_S_Y"

        assert msr1 < msr2, "Less than: Same time but different sourceid (subsource)"
        assert msr1 <= msr2, "Less than: Same time but different sourceid (subsource)"
        assert msr2 > msr1, "Less than: Same time but different sourceid (subsource)"
        assert msr2 >= msr1, "Less than: Same time but different sourceid (subsource)"

    def test_different_time_same_sourceid(self):
        msr1 = MS3Record()
        msr1.set_starttime_str("2023-01-02T01:02:03.123456789Z")
        msr1.sourceid = "FDSN:XX_TEST__B_S_X"

        msr2 = MS3Record()
        msr2.set_starttime_str("2023-01-02T01:02:04.123456789Z")  # 1 second later
        msr2.sourceid = "FDSN:XX_TEST__B_S_X"

        assert msr1 < msr2, "Less than: Different time but same sourceid"
        assert msr1 <= msr2, "Less than equal: Different time but same sourceid"
        assert msr2 > msr1, "Less than: Different time but same sourceid"
        assert msr2 >= msr1, "Less than: Different time but same sourceid"

    def test_empty_location_last(self):
        msr1 = MS3Record()
        msr1.set_starttime_str("2023-01-02T01:02:03.123456789Z")
        msr1.sourceid = "FDSN:XX_TEST_00_B_S_X"

        msr2 = MS3Record()
        msr2.set_starttime_str("2023-01-02T01:02:03.123456789Z")
        msr2.sourceid = "FDSN:XX_TEST_ZZ_B_S_Y"

        msr3 = MS3Record()
        msr3.set_starttime_str("2023-01-02T01:02:03.123456789Z")
        msr3.sourceid = "FDSN:XX_TEST__B_S_Y"

        assert (
            msr1 < msr2 < msr3
        ), "Less than: Same time but different sourceid (location)"
        assert (
            msr1 <= msr2 <= msr3
        ), "Less than equal: Same time but different sourceid (location)"
        assert (
            msr3 > msr2 > msr1
        ), "Greater than: Same time but different sourceid (location)"
        assert (
            msr3 >= msr2 >= msr1
        ), "Greater than equal: Same time but different sourceid (location)"

def test_msrecord_pack():

    # Test populating an MS3Record object with setters
    msr = MS3Record()
    msr.reclen = 512
    msr.sourceid = "FDSN:XX_TEST__B_S_X"
    msr.formatversion = 3
    msr.flags = ct.c_uint8(0x04).value  # Set the 4th bit (clock locked) to 1
    msr.set_starttime_str("2023-01-02T01:02:03.123456789Z")
    msr.samprate = 50.0
    msr.encoding = DataEncoding.STEIM2  # value of 11
    msr.pubversion = 1
    msr.extra = json.dumps({"FDSN": {"Time": {"Quality": 80}}})

    assert msr.reclen == 512
    assert msr.sourceid == "FDSN:XX_TEST__B_S_X"
    assert msr.formatversion == 3
    assert msr.flags_dict() == {'clock_locked': True}
    assert msr.starttime == 1672621323123456789
    assert msr.starttime_seconds == 1672621323.1234567
    assert msr.samprate == 50.0
    assert msr.encoding == DataEncoding.STEIM2
    assert msr.pubversion == 1
    assert msr.extra == '{"FDSN":{"Time":{"Quality":80}}}'

    # Test packing of an miniSEED v3 record
    (packed_samples, packed_records) = msr.pack(record_handler,
                                                datasamples=sine_500,
                                                sampletype='i')

    assert packed_samples == 500
    assert packed_records == 1
    assert len(record_buffer) == 475

    with open(test_pack3, 'rb') as f:
        record_v3 = f.read()
        assert (record_buffer == record_v3)

    # Test packing of an miniSEED v2 record
    msr.formatversion = 2

    (packed_samples, packed_records) = msr.pack(record_handler,
                                                datasamples=sine_500,
                                                sampletype='i')

    assert packed_samples == 500
    assert packed_records == 1
    assert len(record_buffer) == 512

    with open(test_pack2, 'rb') as f:
        record_v2 = f.read()
        assert (record_buffer == record_v2)
