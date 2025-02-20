import pytest
import os
import math
from mseedlib import (
    MSTraceList,
    TimeFormat,
    SubSecond,
    timestr2nstime,
    sampletime,
    MseedLibError,
)

test_dir = os.path.abspath(os.path.dirname(__file__))
test_path3 = os.path.join(test_dir, "data", "testdata-COLA-signal.mseed3")


def test_tracelist_read():
    mstl = MSTraceList(test_path3, unpack_data=True)

    assert mstl.numtraceids == 3

    assert mstl.sourceids() == [
        "FDSN:IU_COLA_00_B_H_1",
        "FDSN:IU_COLA_00_B_H_2",
        "FDSN:IU_COLA_00_B_H_Z",
    ]

    # Fetch first traceID
    traceid = next(mstl.traceids())

    assert traceid.sourceid == "FDSN:IU_COLA_00_B_H_1"
    assert traceid.pubversion == 4
    assert traceid.earliest == 1267253400019539000
    assert traceid.earliest_seconds == 1267253400.019539
    assert traceid.latest == 1267257599969538000
    assert traceid.latest_seconds == 1267257599.969538

    # Fetch first trace segment
    segment = next(traceid.segments())

    assert segment.starttime == 1267253400019539000
    assert segment.starttime_seconds == 1267253400.019539
    assert segment.endtime == 1267257599969538000
    assert segment.endtime_seconds == 1267257599.969538
    assert segment.samprate == 20.0
    assert segment.samplecnt == 84000
    assert segment.numsamples == 84000
    assert segment.sampletype == "i"

    # Data sample array tests
    data = segment.datasamples

    # Check first 6 samples
    assert data[0:6] == [-502916, -502808, -502691, -502567, -502433, -502331]

    # Check last 6 samples
    assert data[-6:] == [-929184, -928936, -928632, -928248, -927779, -927206]

    # Search for a specific TraceID
    foundid = mstl.get_traceid("FDSN:IU_COLA_00_B_H_Z")

    assert foundid.sourceid == "FDSN:IU_COLA_00_B_H_Z"
    assert foundid.pubversion == 4
    assert foundid.earliest == 1267253400019539000
    assert foundid.earliest_seconds == 1267253400.019539
    assert foundid.latest == 1267257599969538000
    assert foundid.latest_seconds == 1267257599.969538

    foundseg = next(foundid.segments())

    # Check first 6 samples
    assert foundseg.datasamples[0:6] == [
        -231394,
        -231367,
        -231376,
        -231404,
        -231437,
        -231474,
    ]

    # Check last 6 samples
    assert foundseg.datasamples[-6:] == [
        -165263,
        -162103,
        -159002,
        -155907,
        -152810,
        -149774,
    ]


def test_tracelist_numpy():
    pytest.importorskip("numpy")
    import numpy as np

    with pytest.raises(ValueError):
        # Must specify unpack_data=True
        mstl = MSTraceList(test_path3)
        traceid = next(mstl.traceids())
        segment = next(traceid.segments())
        np_data = segment.np_datasamples

    mstl = MSTraceList(test_path3, record_list=True)

    # Fetch first traceID
    traceid = next(mstl.traceids())

    # Fetch first trace segment
    segment = next(traceid.segments())

    # Data sample array tests
    np_data = segment.np_datasamples

    # FIXME add assert for int type

    # Check first 6 samples
    assert np.all(
        np_data[0:6] == [-502916, -502808, -502691, -502567, -502433, -502331]
    )

    # Check last 6 samples
    assert np.all(
        np_data[-6:] == [-929184, -928936, -928632, -928248, -927779, -927206]
    )

    # Search for a specific TraceID
    foundid = mstl.get_traceid("FDSN:IU_COLA_00_B_H_Z")

    assert foundid.sourceid == "FDSN:IU_COLA_00_B_H_Z"
    foundseg = next(foundid.segments())

    # Check first 6 samples
    assert np.all(
        foundseg.np_datasamples[0:6]
        == [
            -231394,
            -231367,
            -231376,
            -231404,
            -231437,
            -231474,
        ]
    )

    # Check last 6 samples
    assert np.all(
        foundseg.np_datasamples[-6:]
        == [
            -165263,
            -162103,
            -159002,
            -155907,
            -152810,
            -149774,
        ]
    )


def test_tracelist_read_recordlist():
    mstl = MSTraceList(test_path3, unpack_data=False, record_list=True)

    assert mstl.numtraceids == 3

    assert mstl.sourceids() == [
        "FDSN:IU_COLA_00_B_H_1",
        "FDSN:IU_COLA_00_B_H_2",
        "FDSN:IU_COLA_00_B_H_Z",
    ]

    # Search for a specific trace ID
    foundid = mstl.get_traceid("FDSN:IU_COLA_00_B_H_Z")

    foundseg = next(foundid.segments())

    assert foundseg.numsamples == 0

    # Unpack data samples using in-place buffer
    foundseg.unpack_recordlist()

    assert foundseg.numsamples == 84000

    # Check first 6 samples
    assert foundseg.datasamples[0:6] == [
        -231394,
        -231367,
        -231376,
        -231404,
        -231437,
        -231474,
    ]

    # Check last 6 samples
    assert foundseg.datasamples[-6:] == [
        -165263,
        -162103,
        -159002,
        -155907,
        -152810,
        -149774,
    ]


# A sine wave generator
def sine_generator(start_degree=0, yield_count=100, total=1000):
    """A generator returning a continuing sequence for a sine values."""
    generated = 0
    while generated < total:
        bite_size = min(yield_count, total - generated)

        # Yield a tuple of 3 lists of continuing sine values
        yield list(
            map(
                lambda x: int(math.sin(math.radians(x)) * 500),
                range(start_degree, start_degree + bite_size),
            )
        )

        start_degree += bite_size
        generated += bite_size


# A global record buffer
record_buffer = bytearray()


def record_handler(record, handler_data):
    """A callback function for MSTraceList.set_record_handler()
    Adds the record to a global buffer for testing
    """
    global record_buffer
    record_buffer.extend(bytes(record))


test_pack3 = os.path.join(test_dir, "data", "packtest_sine2000.mseed3")


def test_mstracelist_pack():
    # Create a new MSTraceList object
    mstl = MSTraceList()

    total_samples = 0
    total_records = 0
    sample_rate = 40.0
    start_time = timestr2nstime("2024-01-01T15:13:55.123456789Z")
    format_version = 3
    record_length = 512

    for new_data in sine_generator(yield_count=100, total=2000):

        mstl.add_data(
            sourceid="FDSN:XX_TEST__B_S_X",
            data_samples=new_data,
            sample_type="i",
            sample_rate=sample_rate,
            start_time=start_time,
        )

        start_time = sampletime(start_time, len(new_data), sample_rate)

        (packed_samples, packed_records) = mstl.pack(
            record_handler,
            flush_data=False,
            format_version=format_version,
            record_length=record_length,
        )

        total_samples += packed_samples
        total_records += packed_records

    (packed_samples, packed_records) = mstl.pack(
        record_handler, format_version=format_version, record_length=record_length
    )

    total_samples += packed_samples
    total_records += packed_records

    assert total_samples == 2000
    assert total_records == 5

    with open(test_pack3, "rb") as f:
        data_v3 = f.read()
        assert record_buffer == data_v3


def test_mstracelist_nosuchfile():
    with pytest.raises(MseedLibError):
        mstl = MSTraceList("NOSUCHFILE")
