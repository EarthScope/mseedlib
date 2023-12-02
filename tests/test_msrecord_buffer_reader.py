import pytest
import os
from mseedlib import MSRecordBufferReader, TimeFormat, SubSecond
from mseedlib.exceptions import MseedLibError

test_dir = os.path.abspath(os.path.dirname(__file__))
test_path3 = os.path.join(test_dir, 'data', 'testdata-COLA-signal.mseed3')
test_path2 = os.path.join(test_dir, 'data', 'testdata-COLA-signal.mseed2')


def test_msrecord_read_buffer_details():
    # Read data from test file into a buffer
    with open(test_path3, 'rb') as fp:
        buffer = bytearray(fp.read())

        with MSRecordBufferReader(buffer, unpack_data=True) as msreader:

            # Read first record
            msr = msreader.read()

            assert msr.record_length == 542
            assert msr.swap_flag == 2
            assert msr.swap_flag_dict() == {'header_swapped': False, 'payload_swapped': True}
            assert msr.sourceid == 'FDSN:IU_COLA_00_B_H_1'
            assert msr.format_version == 3
            assert msr.flags == 4
            assert msr.flags_dict() == {'clock_locked': True}
            assert msr.start_time == 1267253400019539000
            assert msr.start_time_seconds == 1267253400.019539
            assert msr.start_time_str(timeformat=TimeFormat.ISOMONTHDAY_Z) == '2010-02-27T06:50:00.019539Z'
            assert msr.start_time_str(timeformat=TimeFormat.SEEDORDINAL,
                                      subsecond=SubSecond.NONE) == '2010,058,06:50:00'
            assert msr.sample_rate == 20.0
            assert msr.sample_rate_raw == 20.0
            assert msr.encoding == 11
            assert msr.encoding_str() == 'STEIM-2 integer compression'
            assert msr.pub_version == 4
            assert msr.sample_count == 296
            assert msr.crc == 1977151071
            assert msr.extra_length == 33
            assert msr.data_length == 448
            assert msr.extra_headers == '{"FDSN":{"Time":{"Quality":100}}}'
            assert msr.data_size == 1184
            assert msr.number_samples == 296
            assert msr.sample_type == 'i'
            assert msr.end_time == 1267253414769539000
            assert msr.end_time_seconds == 1267253414.769539

            # Data sample array tests
            data = msr.data_samples

            # Check first 6 samples
            assert data[0:6] == [-502916, -502808, -502691, -502567, -502433, -502331]

            # Check last 6 samples
            assert data[-6:] == [-508722, -508764, -508809, -508866, -508927, -508986]


def test_msrecord_read_buffer_summary():
    # Read data from test file into a buffer
    with open(test_path2, 'rb') as fp:
        buffer = bytearray(fp.read())

        with MSRecordBufferReader(buffer) as msreader:

            record_count = 0
            sample_count = 0

            for msr in msreader:
                record_count += 1
                sample_count += msr.sample_count

            assert record_count == 1141
            assert sample_count == 252000
