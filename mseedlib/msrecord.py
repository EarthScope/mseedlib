import ctypes as ct
from .clib import clibmseed, wrap_function
from .definitions import *
from .util import ms_nstime2timestr, ms_timestr2nstime, ms_encodingstr
from .exceptions import *
from json import dumps as json_dumps


class MSRecord():
    '''A miniSEED record base class'''

    def __init__(self, msr_pointer=None):
        self._record_handler = None

        self._msr3_init = wrap_function(clibmseed, 'msr3_init', ct.POINTER(MS3Record),
                                        [ct.POINTER(MS3Record)])

        self._msr3_free = wrap_function(clibmseed, 'msr3_free', None,
                                        [ct.POINTER(ct.POINTER(MS3Record))])

        self._msr3_sampratehz = wrap_function(clibmseed, 'msr3_sampratehz', ct.c_double,
                                              [ct.POINTER(MS3Record)])

        self._msr3_print = wrap_function(clibmseed, 'msr3_print', None,
                                         [ct.POINTER(MS3Record), ct.c_int8])

        self._msr3_endtime = wrap_function(clibmseed, 'msr3_endtime', ct.c_int64,
                                           [ct.POINTER(MS3Record)])

        self._mseh_replace = wrap_function(clibmseed, 'mseh_replace', ct.c_int,
                                           [ct.POINTER(MS3Record), ct.c_char_p])

        self._msr3_pack = wrap_function(clibmseed, 'msr3_pack', ct.c_int,
                                        [ct.POINTER(MS3Record), ct.c_void_p, ct.c_void_p,
                                         ct.POINTER(ct.c_int64),
                                         ct.c_uint32, ct.c_int8])

        # Set pointer to MS3Record if supplied or initialize a new one
        if msr_pointer is not None:
            self._msr = msr_pointer
        else:
            self._msr = self._msr3_init(None)

    def __del__(self):
        '''Free memory allocated at the C-level for this MSRecord'''
        self._msr3_free(ct.byref(self._msr))
        self._msr = None

    def __repr__(self):
        return (f'{self.sourceid}, '
                f'{self.pubversion}, '
                f'{self.reclen}, '
                f'{self.samplecnt} samples, '
                f'{self.samprate} Hz, '
                f'{self.starttime_str()}')

    @property
    def reclen(self):
        '''Return record length in bytes'''
        return self._msr.contents.reclen

    @reclen.setter
    def reclen(self, value):
        '''Set maximum record length in bytes'''
        self._msr.contents.reclen = value

    @property
    def swapflag(self):
        '''Return swap flags as raw integer

        Use MSRecord.swap_flag_dict() for a dictionary of decoded flags
        '''
        return self._msr.contents.swapflag

    def swapflag_dict(self):
        '''Return swap flags as dictionary'''
        swapflag = {}
        if self._msr.contents.swapflag & MSSWAP_HEADER.value:
            swapflag['header_swapped'] = True
        else:
            swapflag['header_swapped'] = False
        if self._msr.contents.swapflag & MSSWAP_PAYLOAD.value:
            swapflag['payload_swapped'] = True
        else:
            swapflag['payload_swapped'] = False
        return swapflag

    @property
    def sourceid(self):
        '''Return source identifier as string'''
        return self._msr.contents.sid.decode(encoding="utf-8")

    @sourceid.setter
    def sourceid(self, value):
        '''Set source identifier

        The source identifier is limited to 64 characters.
        Typicall this is an FDSN Source Identifier:
        https://docs.fdsn.org/projects/source-identifiers
        '''
        self._msr.contents.sid = bytes(value, 'utf-8')

    @property
    def formatversion(self):
        '''Return format version'''
        return self._msr.contents.formatversion

    @formatversion.setter
    def formatversion(self, value):
        '''Set format version'''
        if value not in [2, 3]:
            raise ValueError(f'Invalid miniSEED format version: {value}')

        self._msr.contents.formatversion = value

    @property
    def flags(self):
        '''Return record flags as raw 8-bit integer

        Use MSRecord.flags_dict() for a dictionary of decoded flags
        '''
        return self._msr.contents.flags

    @flags.setter
    def flags(self, value):
        '''Set record flags as an 8-bit unsigned integer'''
        self._msr.contents.flags = value

    def flags_dict(self):
        '''Return record flags as a dictionary'''
        flags = {}
        if self._msr.contents.flags & ct.c_uint8(0x01).value:
            flags['calibration_signals_present'] = True
        if self._msr.contents.flags & ct.c_uint8(0x02).value:
            flags['time_tag_is_questionable'] = True
        if self._msr.contents.flags & ct.c_uint8(0x04).value:
            flags['clock_locked'] = True
        return flags

    @property
    def starttime(self):
        '''Return start time as nanoseconds since Unix/POSIX epoch'''
        return self._msr.contents.starttime

    @starttime.setter
    def starttime(self, value):
        '''Set start time as nanoseconds since Unix/POSIX epoch'''
        self._msr.contents.starttime = value

    @property
    def starttime_seconds(self):
        '''Return start time as seconds since Unix/POSIX epoch'''
        return self._msr.contents.starttime / NSTMODULUS

    @starttime_seconds.setter
    def starttime_seconds(self, value):
        '''Set start time as seconds since Unix/POSIX epoch'''
        self._msr.contents.starttime = value * NSTMODULUS

    def starttime_str(self, timeformat=TimeFormat.ISOMONTHDAY_Z, subsecond=SubSecond.NANO_MICRO_NONE):
        '''Return start time as formatted string'''
        c_timestr = ct.create_string_buffer(32)

        ms_nstime2timestr(self._msr.contents.starttime, c_timestr, timeformat, subsecond)

        return str(c_timestr.value, 'utf-8')

    def set_starttime_str(self, value):
        '''Set the start time using the specified provided date-time string'''
        self.starttime = ms_timestr2nstime(bytes(value, 'utf-8'))

        if self.starttime == NSTERROR:
            raise ValueError(f'Invalid start time string: {value}')

    @property
    def samprate(self):
        '''Return sample rate value as samples per second'''
        return self._msr3_sampratehz(self._msr)

    @samprate.setter
    def samprate(self, value):
        '''Set sample rate

        When the value is positive it represents the rate in samples per second,
        when it is negative it represents the sample period in seconds.
        The specification recommends using the negative value sample period notation
        for rates less than 1 samples per second to retain resolution.

        Set to 0.0 if no time series data are included in the record, e.g. header-only
        record or text payload.
        '''
        self._msr.contents.samprate = value

    @property
    def samprate_raw(self):
        '''Return raw sample rate value

        This value represents samples per second when positive and sample interval
        in seconds when negative.  Use MSRecord.samprate() for a consistent value in samples
        per second.
        '''
        return self._msr.contents.samprate

    @property
    def encoding(self):
        '''Return encoding format code.  Use MSRecord.encoding_str() for a readable description'''
        return self._msr.contents.encoding

    @encoding.setter
    def encoding(self, value):
        '''Set encoding format code

        See https://docs.fdsn.org/projects/miniseed3/en/latest/data-encodings.html
        '''
        self._msr.contents.encoding = value

    @property
    def pubversion(self):
        '''Return publication version'''
        return self._msr.contents.pubversion

    @pubversion.setter
    def pubversion(self, value):
        '''Set publication version'''
        self._msr.contents.pubversion = value

    @property
    def samplecnt(self):
        '''Return sample count'''
        return self._msr.contents.samplecnt

    @property
    def crc(self):
        '''Return CRC-32C from record header'''
        return self._msr.contents.crc

    @property
    def extralength(self):
        '''Return length of extra headers'''
        return self._msr.contents.extralength

    @property
    def datalength(self):
        '''Return length of encoded data payload in bytes'''
        return self._msr.contents.datalength

    @property
    def extra(self):
        '''Return extra headers as string

        This is a JSON string, decodable to a dictionary with `json.loads(MSRecord.extra)`
        '''
        return self._msr.contents.extra.decode(encoding='utf-8')

    @extra.setter
    def extra(self, value):
        '''Set extra headers to specified JSON string'''
        status = self._mseh_replace(self._msr, value.encode(encoding='utf-8') if value is not None else None)

        if status < 0:
            raise MseedLibError(status, f'Error replacing extra headers')

    @property
    def datasamples(self):
        '''Return data samples as a ctype array of type `MSRecord.sampletype`

        The returned array can be used directly with slicing and indexing
        from `0` to `MSRecord.numsamples - 1`.

        The array can efficiently be copied to a _python list_ using:

            data_samples = MSRecord.datasamples[:]

        The array can efficiently be copied to a _numpy array_ using:

            # Translate libmseed sample type to numpy type
            nptype = {'i': numpy.int32, 'f': numpy.float32, 'd': numpy.float64, 't': numpy.char}

            numpy.frombuffer(MSRecord.datasamples, dtype=nptype[MSRecord.sampletype])

        *NOTE* These data are owned by the this object instance and will be freed
        when the instance is destroyed.  If you wish to keep the data, you must
        make a copy.
        '''
        if self.numsamples <= 0:
            raise ValueError("No decoded samples available")

        if self.sampletype == 'i':
            return ct.cast(self._msr.contents.datasamples,
                           ct.POINTER(ct.c_int32 * self.numsamples)).contents
        elif self.sampletype == 'f':
            return ct.cast(self._msr.contents.datasamples,
                           ct.POINTER(ct.c_float * self.numsamples)).contents
        elif self.sampletype == 'd':
            return ct.cast(self._msr.contents.datasamples,
                           ct.POINTER(ct.c_double * self.numsamples)).contents
        elif self.sampletype == 't':
            return ct.cast(self._msr.contents.datasamples,
                           ct.POINTER(ct.c_char * self.numsamples)).contents
        else:
            raise ValueError(f"Unknown sample type: {self.sampletype}")

    @property
    def datasize(self):
        '''Return size of decoded data payload in bytes'''
        return self._msr.contents.datasize

    @property
    def numsamples(self):
        '''Return number of decoded samples at MSRecord.datasamples'''
        return self._msr.contents.numsamples

    @property
    def sampletype(self):
        '''Return sample type code'''
        return self._msr.contents.sampletype.decode(encoding='utf-8')

    @property
    def endtime(self):
        '''Return end time as nanoseconds since Unix/POSIX epoch'''
        return self._msr3_endtime(self._msr)

    @property
    def endtime_seconds(self):
        '''Return end time as seconds since Unix/POSIX epoch'''
        return self._msr3_endtime(self._msr) / NSTMODULUS

    def endtime_str(self, timeformat=TimeFormat.ISOMONTHDAY_Z, subsecond=SubSecond.NANO_MICRO_NONE):
        '''Return start time as formatted string'''
        c_timestr = ct.create_string_buffer(32)

        ms_nstime2timestr(self.endtime, c_timestr, timeformat, subsecond)

        return str(c_timestr.value, 'utf-8')

    def encoding_str(self):
        '''Return encoding format as descriptive string'''
        return ms_encodingstr(self._msr.contents.encoding).decode('utf-8')

    def print(self, details=0):
        '''Print details of the record to stdout, with varying levels of `details`'''
        self._msr3_print(self._msr, details)

    def set_record_handler(self, record_handler, handler_data=None):
        '''Set the record handler function and data called by MSRecord.pack()

        The record_handler(record, handler_data) function must accept two arguments:

                record:         A buffer containing a miniSEED record
                handler_data:   The handler_data object passed to MSRecord.set_record_handler()

        The function must use or copy the record buffer as the memory may be reused
        on subsequent iterations.
        '''
        self._record_handler = record_handler
        self._record_handler_data = handler_data

        # Set up ctypes callback function to the wrapper function
        RECORD_HANDLER = ct.CFUNCTYPE(None, ct.POINTER(ct.c_char), ct.c_int, ct.c_void_p)
        self._ctypes_record_handler = RECORD_HANDLER(self._record_handler_wrapper)

    def _record_handler_wrapper(self, record, record_length, handlerdata):
        '''Callback function for msr3_pack()

        The `handlerdata` argument is purposely unused, as handler data is passed
        via the class instance instead of through the C layer.
        '''
        # Cast the record buffer to a ctypes array for use in Python and pass to handler
        self._record_handler(ct.cast(record, ct.POINTER((ct.c_char * record_length))).contents,
                             self._record_handler_data)

    def pack(self, datasamples=None, sampletype=None, flush_data=True, verbose=0) -> (int, int):
        '''Pack `datasamples` into miniSEED record(s) and call `MSRecrod.record_handler()`

        The record_handler() function must be registered with MSRecord.set_record_handler().

        If `datasamples` is not None, it must be a sequence of samples that can be
        packed into the type specified by `sampletype` and appropriate for MSRecord.encoding.
        If `datasamples` is None, any samples associated with the MSRecord will be packed.

        If `flush_data` is True, all data samples will be packed.  In the case of miniSEED
        format version 2, this will likely create an unfilled final record.

        If `flush_data` is False, as many fully-packed records will be created as possible.
        The `datasamples` sequence will _not_ be modified, it is up to the caller to
        adjust the sequence to remove samples that have been packed if desired.

        Returns a tuple of (packed_samples, packed_records)
        '''

        if self._record_handler is None:
            raise ValueError('No record handler function registered, see MSRecord.set_record_handler()')

        pack_flags = ct.c_uint32(0)
        packed_samples = ct.c_int64(0)

        if flush_data:
            pack_flags.value |= MSF_FLUSHDATA.value

        if datasamples is not None:
            msr_datasamples = self._msr.contents.datasamples
            msr_sampletype = self._msr.contents.sampletype
            msr_numsamples = self._msr.contents.numsamples
            msr_samplecnt = self._msr.contents.samplecnt

            len_datasamples = len(datasamples)

            if sampletype == 'i':
                ctypes_data = (ct.c_int32 * len_datasamples)(*datasamples)
            elif sampletype == 'f':
                ctypes_data = (ct.c_float * len_datasamples)(*datasamples)
            elif sampletype == 'd':
                ctypes_data = (ct.c_double * len_datasamples)(*datasamples)
            elif sampletype == 't':
                ctypes_data = (ct.c_char * len_datasamples)(*datasamples)
            else:
                raise ValueError(f"Unknown sample type: {sampletype}")

            self._msr.contents.datasamples = ct.cast(ct.byref(ctypes_data), ct.c_void_p)
            self._msr.contents.sampletype = bytes(sampletype, 'utf-8')
            self._msr.contents.numsamples = len_datasamples
            self._msr.contents.samplecnt = len_datasamples

        packed_records = self._msr3_pack(self._msr, self._ctypes_record_handler, None,
                                         ct.byref(packed_samples), pack_flags, verbose)

        # Restore the original datasamples, stampletype, numsamples, samplecnt
        if datasamples is not None:
            self._msr.contents.datasamples = msr_datasamples
            self._msr.contents.sampletype = msr_sampletype
            self._msr.contents.numsamples = msr_numsamples
            self._msr.contents.samplecnt = msr_samplecnt

        if packed_records < 0:
            raise MseedLibError(packed_records, f'Error packing miniSEED record(s)')

        return (packed_samples.value, packed_records)
