import ctypes as ct
from .clib import clibmseed, wrap_function
from .definitions import *
from .exceptions import *
from .msrecord import MSRecord


class MSRecordBufferReader(MSRecord):
    """Read miniSEED records from a buffer, i.e. bytearray or numpy.array

    The `source` object must be support the writeable buffer interface
    for use with the ctypes interface without making a copy, but this
    class will not modify the buffer.

    If `unpack_data` is True, the data samples will be decoded.

    If `validate_crc` is True, the CRC will be validated if contained in
    the record (legacy miniSEED v2 contains no CRCs).  The CRC provides an
    internal integrity check of the record contents.
    """

    def __init__(self, source, unpack_data=False, validate_crc=True, verbose=0):
        super().__init__()

        self.source = source
        self.source_offset = 0
        self.parse_flags = ct.c_uint32(0)
        self.verbose = ct.c_int8(verbose)

        if unpack_data:
            self.parse_flags.value |= MSF_UNPACKDATA.value

        if validate_crc:
            self.parse_flags.value |= MSF_VALIDATECRC.value

        self.msr3_parse = wrap_function(clibmseed, 'msr3_parse', ct.c_int,
                                                   [ct.POINTER(ct.c_char), ct.c_uint64,
                                                    ct.POINTER(ct.POINTER(MS3Record)),
                                                    ct.c_uint32, ct.c_int8])

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __iter__(self):
        return self

    def __next__(self):
        next = self.read()
        if next is not None:
            return next
        else:
            raise StopIteration

    def read(self):
        remaining_bytes = len(self.source) - self.source_offset
        if remaining_bytes <= 40:
            return None

        status = self.msr3_parse((ct.c_char * (remaining_bytes)).from_buffer(self.source, self.source_offset),
                                 remaining_bytes, ct.byref(self._msr),
                                 self.parse_flags, self.verbose)

        if status == MS_NOERROR:
            self.source_offset += self.record_length
            return self
        elif status > 0:  # Record detected but not enough data
            return None
        else:
            raise MseedLibError(status, f'Error reading miniSEED record')

    def close(self):
        pass