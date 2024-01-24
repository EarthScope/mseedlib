import pytest
import sys
import os
from mseedlib import MS3RecordReader, DataEncoding, TimeFormat, SubSecond
from mseedlib.exceptions import MseedLibError

test_dir = os.path.abspath(os.path.dirname(__file__))
test_path3 = os.path.join(test_dir, 'data', 'testdata-COLA-signal.mseed3')
test_path2 = os.path.join(test_dir, 'data', 'testdata-COLA-signal.mseed2')

def test_msrecord_read_record_details():
    with MS3RecordReader(test_path3, unpack_data=True) as msreader:

        # Read first record
        msr = msreader.read()

        assert msr.reclen == 542
        assert msr.swapflag == 2
        assert msr.swapflag_dict() == {'header_swapped': False, 'payload_swapped': True}
        assert msr.sourceid == 'FDSN:IU_COLA_00_B_H_1'
        assert msr.formatversion == 3
        assert msr.flags == 4
        assert msr.flags_dict() == {'clock_locked': True}
        assert msr.starttime == 1267253400019539000
        assert msr.starttime_seconds == 1267253400.019539
        assert msr.starttime_str(timeformat=TimeFormat.ISOMONTHDAY_Z) == '2010-02-27T06:50:00.019539Z'
        assert msr.starttime_str(timeformat=TimeFormat.SEEDORDINAL, subsecond=SubSecond.NONE) == '2010,058,06:50:00'
        assert msr.samprate == 20.0
        assert msr.samprate_raw == 20.0
        assert msr.encoding == DataEncoding.STEIM2
        assert msr.encoding_str() == 'STEIM-2 integer compression'
        assert msr.pubversion == 4
        assert msr.samplecnt == 296
        assert msr.crc == 1977151071
        assert msr.extralength == 33
        assert msr.datalength == 448
        assert msr.extra == '{"FDSN":{"Time":{"Quality":100}}}'
        assert msr.numsamples == 296
        assert msr.sampletype == 'i'
        assert msr.endtime == 1267253414769539000
        assert msr.endtime_seconds == 1267253414.769539

        # Data sample array tests
        data = msr.datasamples

        # Check first 6 samples
        assert data[0:6] == [-502916, -502808, -502691, -502567, -502433, -502331]

        # Check last 6 samples
        assert data[-6:] == [-508722, -508764, -508809, -508866, -508927, -508986]

def test_msrecord_read_record_details_fd():
    # Open a file descriptor in python and provide the open stream to the reader

    # File descriptor support is not implemented on Windows
    if sys.platform.lower().startswith("win"):
        return

    # Using a file for tesing, but this could be stdin or any other input stream
    fp = open(test_path2, 'rb', buffering=0)

    # Provide the reader with the file descriptor
    with MS3RecordReader(fp.fileno(), unpack_data=True) as msreader:
        # Read first record
        msr = msreader.read()

        # Data sample array tests
        data = msr.datasamples

        # Check first 6 samples
        assert data[0:6] == [-502916, -502808, -502691, -502567, -502433, -502331]

        # Check last 6 samples
        assert data[-6:] == [-508722, -508764, -508809, -508866, -508927, -508986]

def test_msrecord_read_records_summary():
    with MS3RecordReader(test_path2) as msreader:

        record_count = 0
        sample_count = 0

        for msr in msreader:
            record_count += 1
            sample_count += msr.samplecnt

        assert record_count == 1141
        assert sample_count == 252000

def test_msrecord_nosuchfile():
    with pytest.raises(MseedLibError):
        with MS3RecordReader("NOSUCHFILE") as msreader:
            msr = msreader.read()
