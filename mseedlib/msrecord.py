import ctypes as ct
import array as arr
from .clib import clibmseed, wrap_function
from .definitions import *
from .util import ms_nstime2timestr, ms_encodingstr
from .exceptions import *
from json import loads as json_loads, dumps as json_dumps


class MSRecord():

    def __init__(self):
        super().__init__()

        self.msr = ct.POINTER(MS3Record)()  # Creates a NULL pointer, testable as boolean False

        self.msr3_sampratehz = wrap_function(clibmseed, 'msr3_sampratehz', ct.c_double,
                                             [ct.POINTER(MS3Record)])

        self.msr3_print = wrap_function(clibmseed, 'msr3_print', None,
                                        [ct.POINTER(MS3Record), ct.c_int8])

        self.msr3_endtime = wrap_function(clibmseed, 'msr3_endtime', ct.c_int64,
                                          [ct.POINTER(MS3Record)])

    def __repr__(self):
        if not self.msr:
            raise ValueError("No miniSEED record information present")

        return (f'{self.sourceid()}, '
                f'{self.pub_version()}, '
                f'{self.record_length()}, '
                f'{self.sample_count()} samples, '
                f'{self.sample_rate()} Hz, '
                f'{self.start_time_str()}')

    def record_length(self):
        '''Return record length in bytes'''
        if not self.msr:
            raise ValueError("No miniSEED record information present")

        return self.msr.contents.reclen

    def swap_flag(self, raw=False):
        '''Return swap flags as dictionary (default), or optionally as a `raw` integer'''
        if not self.msr:
            raise ValueError("No miniSEED record information present")

        if raw:
            return self.msr.contents.swapflag
        else:
            swap_flags = {}

            if self.msr.contents.swapflag & MSSWAP_HEADER.value:
                swap_flags['header_swapped'] = True
            else:
                swap_flags['header_swapped'] = False

            if self.msr.contents.swapflag & MSSWAP_PAYLOAD.value:
                swap_flags['payload_swapped'] = True
            else:
                swap_flags['payload_swapped'] = False

            return swap_flags

    def sourceid(self):
        '''Return source identifier as string'''
        if not self.msr:
            raise ValueError("No miniSEED record information present")

        return self.msr.contents.sid.decode(encoding="utf-8")

    def format_version(self):
        '''Return format version'''
        if not self.msr:
            raise ValueError("No miniSEED record information present")

        return self.msr.contents.formatversion

    def flags(self, raw=False):
        '''Return record flags'''
        if not self.msr:
            raise ValueError("No miniSEED record information present")

        if raw:
            return self.msr.contents.flags
        else:
            flags = {}

            if self.msr.contents.flags & ct.c_uint8(0x01).value:
                flags['calibration_signals_present'] = True
            if self.msr.contents.flags & ct.c_uint8(0x02).value:
                flags['time_tag_is_questionable'] = True
            if self.msr.contents.flags & ct.c_uint8(0x04).value:
                flags['clock_locked'] = True

            return flags

    def start_time(self, seconds=False):
        '''Return start time as nanoseconds (default), or optionally `seconds`, since Unix/POSIX epoch'''
        if not self.msr:
            raise ValueError("No miniSEED record information present")

        if seconds:
            return self.msr.contents.starttime / NSTMODULUS
        else:
            return self.msr.contents.starttime

    def sample_rate(self, raw=False):
        '''Return sample rate value, either `raw` value or samples per second'''
        if not self.msr:
            raise ValueError("No miniSEED record information present")

        if raw:
            return self.msr.contents.samprate
        else:
            return self.msr3_sampratehz(self.msr)

    def encoding(self):
        '''Return encoding format code.  Use ms_encoding_str() for a readable description'''
        if not self.msr:
            raise ValueError("No miniSEED record information present")

        return self.msr.contents.encoding

    def pub_version(self):
        '''Return publication version'''
        if not self.msr:
            raise ValueError("No miniSEED record information present")

        return self.msr.contents.pubversion

    def sample_count(self):
        '''Return sample count'''
        if not self.msr:
            raise ValueError("No miniSEED record information present")

        return self.msr.contents.samplecnt

    def crc(self):
        '''Return CRC-32C from record header'''
        if not self.msr:
            raise ValueError("No miniSEED record information present")

        return self.msr.contents.crc

    def extra_length(self):
        '''Return length of extra headers'''
        if not self.msr:
            raise ValueError("No miniSEED record information present")

        return self.msr.contents.extralength

    def data_length(self):
        '''Return length of encoded data payload in bytes'''
        if not self.msr:
            raise ValueError("No miniSEED record information present")

        return self.msr.contents.datalength

    def extra_headers(self, raw=False):
        '''Return extra headers as dictionary (default), or optionally as a `raw` JSON string'''
        if not self.msr:
            raise ValueError("No miniSEED record information present")

        if raw:
            return self.msr.contents.extra.decode(encoding='utf-8')
        else:
            return json_loads(self.msr.contents.extra.decode(encoding='utf-8'))

    def data_samples(self):
        '''Return data samples as a ctype array of type `sample_type`

        NOTE: These data are owned by the MSRecord object and will be freed
        when the object is destroyed.  If you wish to keep the data, you must
        make a copy.
        '''
        if not self.msr:
            raise ValueError("No miniSEED record information present")

        number_samples = self.number_samples()

        if number_samples <= 0:
            raise ValueError("No decoded samples available")

        if self.sample_type() == 'i':
            return ct.cast(self.msr.contents.datasamples,
                           ct.POINTER(ct.c_int32 * self.number_samples())).contents
        elif self.sample_type() == 'f':
            return ct.cast(self.msr.contents.datasamples,
                           ct.POINTER(ct.c_float * self.number_samples())).contents
        elif self.sample_type() == 'd':
            return ct.cast(self.msr.contents.datasamples,
                           ct.POINTER(ct.c_double * self.number_samples())).contents
        elif self.sample_type() == 't':
            return ct.cast(self.msr.contents.datasamples,
                           ct.POINTER(ct.c_char * self.number_samples())).contents
        else:
            raise ValueError(f"Unknown sample type: {self.sample_type()}")

    def data_size(self):
        '''Return size of decoded data payload in bytes'''
        if not self.msr:
            raise ValueError("No miniSEED record information present")

        return self.msr.contents.datasize

    def number_samples(self):
        '''Return number of decoded samples'''
        if not self.msr:
            raise ValueError("No miniSEED record information present")

        return self.msr.contents.numsamples

    def sample_type(self):
        '''Return sample type code'''
        if not self.msr:
            raise ValueError("No miniSEED record information present")

        return self.msr.contents.sampletype.decode(encoding='utf-8')

    def end_time(self, seconds=False):
        '''Return end time as nanoseconds (default), or optionally seconds, since Unix/POSIX epoch'''
        if not self.msr:
            raise ValueError("No miniSEED record information present")

        if seconds:
            return self.msr3_endtime(self.msr) / NSTMODULUS
        else:
            return self.msr3_endtime(self.msr)

    def start_time_str(self, timeformat=TimeFormat.ISOMONTHDAY_Z, subsecond=SubSecond.NANO_MICRO_NONE):
        '''Return start time as formatted string'''
        if not self.msr:
            raise ValueError("No miniSEED record information present")

        c_timestr = ct.create_string_buffer(32)

        ms_nstime2timestr(self.msr.contents.starttime, c_timestr, timeformat, subsecond)

        return str(c_timestr.value, 'utf-8')

    def encoding_str(self):
        '''Return encoding format as string'''
        if not self.msr:
            raise ValueError("No miniSEED record information present")

        return ms_encodingstr(self.msr.contents.encoding).decode('utf-8')

    def print(self, details=0):
        '''Print details of the record'''
        if not self.msr:
            raise ValueError("No miniSEED record information present")

        self.msr3_print(self.msr, details)
