import pytest
import os
from mseedlib import MSTraceList, TimeFormat, SubSecond
from mseedlib.exceptions import MseedLibError

test_dir = os.path.abspath(os.path.dirname(__file__))
test_path3 = os.path.join(test_dir, 'data', 'testdata-COLA-signal.mseed3')


def test_tracelist_read():
    mstl = MSTraceList(test_path3, unpack_data=True)

    assert mstl.numtraceids == 3

    assert mstl.sourceids() == ['FDSN:IU_COLA_00_B_H_1', 'FDSN:IU_COLA_00_B_H_2', 'FDSN:IU_COLA_00_B_H_Z']

    # Fetch first traceID
    traceid = next(mstl.traceids())

    assert traceid.sourceid == 'FDSN:IU_COLA_00_B_H_1'
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
    assert segment.datasize == 336000
    assert segment.numsamples == 84000
    assert segment.sampletype == 'i'

    # Data sample array tests
    data = segment.datasamples

    # Check first 6 samples
    assert data[0:6] == [-502916, -502808, -502691, -502567, -502433, -502331]

    # Check last 6 samples
    assert data[-6:] == [-929184, -928936, -928632, -928248, -927779, -927206]

    # Search for a specific TraceID
    foundid = mstl.get_traceid('FDSN:IU_COLA_00_B_H_Z')

    assert foundid.sourceid == 'FDSN:IU_COLA_00_B_H_Z'
    assert foundid.pubversion == 4
    assert foundid.earliest == 1267253400019539000
    assert foundid.earliest_seconds == 1267253400.019539
    assert foundid.latest == 1267257599969538000
    assert foundid.latest_seconds == 1267257599.969538

    foundseg = next(foundid.segments())

    # Check first 6 samples
    assert foundseg.datasamples[0:6] == [-231394, -231367, -231376, -231404, -231437, -231474]

    # Check last 6 samples
    assert foundseg.datasamples[-6:] == [-165263, -162103, -159002, -155907, -152810, -149774]

def test_tracelist_read_tracelist():
    mstl = MSTraceList(test_path3, unpack_data=False, record_list=True)

    assert mstl.numtraceids == 3

    assert mstl.sourceids() == ['FDSN:IU_COLA_00_B_H_1', 'FDSN:IU_COLA_00_B_H_2', 'FDSN:IU_COLA_00_B_H_Z']

    # Search for a specific trace ID
    foundid = mstl.get_traceid('FDSN:IU_COLA_00_B_H_Z')

    foundseg = next(foundid.segments())

    assert foundseg.numsamples == 0

    # Unpack data samples using in-place buffer
    foundseg.unpack_recordlist()

    assert foundseg.numsamples == 84000

    # Check first 6 samples
    assert foundseg.datasamples[0:6] == [-231394, -231367, -231376, -231404, -231437, -231474]

    # Check last 6 samples
    assert foundseg.datasamples[-6:] == [-165263, -162103, -159002, -155907, -152810, -149774]


def test_msrecord_nosuchfile():
    with pytest.raises(MseedLibError):
        mstl = MSTraceList("NOSUCHFILE")
