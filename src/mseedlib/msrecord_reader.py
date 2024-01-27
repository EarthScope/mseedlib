import sys
import ctypes as ct
from .clib import clibmseed, wrap_function
from .definitions import *
from .exceptions import *
from .msrecord import MS3Record


class MS3RecordReader():
    """Read miniSEED records from a file or file descriptor

    If `input` is an integer, it is assumed to be an open file descriptor,
    otherwise it is assumed to be a path (file) name.  In all cases the
    file or descriptor will be closed when the objects close() is called.

    If `unpack_data` is True, the data samples will be decoded.

    If `skip_not_data` is True, bytes from the input stream will be skipped
    until a record is found.

    If `validate_crc` is True, the CRC will be validated if contained in
    the record (legacy miniSEED v2 contains no CRCs).  The CRC provides an
    internal integrity check of the record contents.
    """

    def __init__(self, input, unpack_data=False, skip_not_data=False,
                 validate_crc=True, verbose=0):
        super().__init__()

        self._msfp = ct.c_void_p(None)
        self._msr = ct.c_void_p(None)
        self._selections = ct.c_void_p()
        self.parse_flags = ct.c_uint32(0)
        self.verbose = ct.c_int8(verbose)

        if unpack_data:
            self.parse_flags.value |= MSF_UNPACKDATA.value

        if skip_not_data:
            self.parse_flags.value |= MSF_SKIPNOTDATA.value

        if validate_crc:
            self.parse_flags.value |= MSF_VALIDATECRC.value

        self.ms3_readmsr_selection = wrap_function(clibmseed, 'ms3_readmsr_selection', ct.c_int,
                                                   [ct.POINTER(ct.c_void_p),
                                                    ct.POINTER(ct.c_void_p),
                                                    ct.c_char_p, ct.c_uint32, ct.c_void_p, ct.c_int8])

        self.ms3_mstl_init_fd = wrap_function(clibmseed, 'ms3_mstl_init_fd', ct.c_void_p,
                                              [ct.c_int])

        # If the stream is an integer, assume an open file descriptor
        if isinstance(input, int):
            if sys.platform.lower().startswith("win"):
                raise NotImplementedError('File descriptor support not implemented on Windows')

            self._msfp = ct.c_void_p(self.ms3_mstl_init_fd(input))
            self.stream_name = bytes(f'File Descriptor {input}', 'utf-8')

            if self._msfp is None:
                raise MseedLibError(MS_GENERROR, f'Error initializing file descriptor {input}')

        # Otherwise, assume a path name
        else:
            self.stream_name = bytes(input, 'utf-8')

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

    def read(self) -> MS3Record:
        status = self.ms3_readmsr_selection(ct.byref(self._msfp), ct.byref(self._msr),
                                            self.stream_name, self.parse_flags, self._selections, self.verbose)

        if status == MS_NOERROR:
            return ct.cast(self._msr, ct.POINTER(MS3Record)).contents
        elif status == MS_ENDOFFILE:
            return None
        else:
            raise MseedLibError(status, f'Error reading miniSEED record')

    def close(self) -> None:
        self.ms3_readmsr_selection(ct.byref(self._msfp), ct.byref(self._msr),
                                   None, self.parse_flags, self._selections, self.verbose)
