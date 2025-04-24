import pytest
from mseedlib import MS3Record
from mseedlib.msrecord_buffer_compare import (
    sort_mseed_content,
    compare_miniseed_content,
)

from .conftest import sine_500

# A global record buffer
record_buffer = b""


@pytest.fixture(scope="module")
def msr_XX_TEST__B_S_X_bytes() -> tuple(MS3Record, bytes):
    msr1 = MS3Record()
    msr1.set_starttime_str("2023-01-02T01:02:03.123456789Z")
    msr1.sourceid = "FDSN:XX_TEST__B_S_X"
    msr1.pack(record_handler, datasamples=sine_500, sampletype="i")
    msr1_bytes = bytes(record_buffer)  # Make a copy of the packed record
    return msr1, msr1_bytes


@pytest.fixture(scope="module")
def msr_XX_TEST__B_S_Y_bytes() -> tuple(MS3Record, bytes):
    msr1 = MS3Record()
    msr1.set_starttime_str("2023-01-02T01:02:03.123456789Z")
    msr1.sourceid = "FDSN:XX_TEST__B_S_X"
    msr1.pack(record_handler, datasamples=sine_500, sampletype="i")
    msr1_bytes = bytes(record_buffer)  # Make a copy of the packed record
    return msr1, msr1_bytes


def record_handler(record, handler_data):
    """A callback function for MS3Record.set_record_handler()
    Stores the record in a global buffer for testing
    """
    print("Record handler called, record length: %d" % len(record))
    global record_buffer
    record_buffer = bytes(record)


def test_sort_mseed_content():
    """Test sorting of miniSEED content"""

    msr1 = MS3Record()
    msr1.set_starttime_str("2023-01-02T01:02:03.123456789Z")
    msr1.sourceid = "FDSN:XX_TEST__B_S_X"
    msr1.pack(record_handler, datasamples=sine_500, sampletype="i")
    msr1_bytes = bytes(record_buffer)  # Make a copy of the packed record

    msr2 = MS3Record()
    msr2.set_starttime_str("2023-01-02T01:02:03.123456789Z")
    msr2.sourceid = "FDSN:XX_TEST__B_S_Y"
    msr2.pack(record_handler, datasamples=sine_500, sampletype="i")
    msr2_bytes = bytes(record_buffer)  # Make a copy of the packed record

    expected_sorted_bytes = msr1_bytes + msr2_bytes
    unsorted_bytes = msr2_bytes + msr1_bytes

    sorted_bytes = sort_mseed_content(unsorted_bytes)

    assert (
        sorted_bytes == expected_sorted_bytes
    ), "Sorted bytes do not match expected order"


class TestCompareMiniseed:
    def test_sorting():
        pass
