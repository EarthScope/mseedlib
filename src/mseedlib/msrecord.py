import ctypes as ct
import json
from typing import Optional, Any
from .clib import clibmseed, wrap_function
from .definitions import *
from .util import ms_nstime2timestr, ms_timestr2nstime, ms_encodingstr
from .exceptions import *


class MS3Record(ct.Structure):
    """A miniSEED record base class mirroring libmseed's MS3Record structure"""

    _fields_ = [
        ("_record", ct.POINTER(ct.c_char)),  # Raw miniSEED record, if available
        ("_reclen", ct.c_int32),  # Length of miniSEED record in bytes
        ("_swapflag", ct.c_uint8),  # Byte swap indicator (bitmask)
        ("_sid", ct.c_char * LM_SIDLEN),  # Source identifier
        ("_formatversion", ct.c_uint8),  # Format major version
        ("_flags", ct.c_uint8),  # Record-level bit flags
        ("_starttime", ct.c_int64),  # Record start time (first sample)
        (
            "_samprate",
            ct.c_double,
        ),  # Nominal sample rate as samples/second (Hz) or period (s)
        ("_encoding", ct.c_int16),  # Data encoding format code
        ("_pubversion", ct.c_uint8),  # Publication version
        ("_samplecnt", ct.c_int64),  # Number of samples in record
        ("_crc", ct.c_uint32),  # CRC of entire record
        ("_extralength", ct.c_uint16),  # Length of extra headers in bytes
        ("_datalength", ct.c_uint32),  # Length of datasamples buffer in bytes
        ("_extra", ct.c_char_p),  # Pointer to extra headers (JSON)
        (
            "_datasamples",
            ct.c_void_p,
        ),  # Data samples, 'numsamples' of type 'sampletype'
        ("_datasize", ct.c_uint64),  # Size of datasamples buffer in bytes
        ("_numsamples", ct.c_int64),  # Number of data samples in 'datasamples'
        ("_sampletype", ct.c_char),
    ]  # Sample type code: t (text), i (int32) , f (float), d (double)

    # Set defaults matching msr3_init()
    def __init__(self, reclen=-1, encoding=-1, samplecnt=-1):
        super().__init__(_reclen=reclen, _encoding=encoding, _samplecnt=samplecnt)

    def __repr__(self) -> str:
        datasamples_str = "[]"
        if self._numsamples > 0:
            samples = self.datasamples
            datasamples_str = (
                str(samples[:5]) + " ..." if len(samples) > 5 else str(samples)
            )

        return (
            f"MS3Record(sourceid: {self._sid}\n"
            f"        pubversion: {self._pubversion}\n"
            f"            reclen: {self._reclen}\n"
            f"     formatversion: {self._formatversion}\n"
            f"         starttime: {self._starttime} => {self.starttime_str()}\n"
            f"         samplecnt: {self._samplecnt}\n"
            f"          samprate: {self._samprate}\n"
            f"             flags: {self._flags} => {self.flags_dict()}\n"
            f"               CRC: {self._crc} => {hex(self._crc)}\n"
            f"          encoding: {self._encoding} => {self.encoding_str()}\n"
            f"       extralength: {self._extralength}\n"
            f"        datalength: {self._datalength}\n"
            f"             extra: {self._extra}\n"
            f"        numsamples: {self._numsamples}\n"
            f"       datasamples: {datasamples_str}\n"  # Need to limit this to a few samples
            f"          datasize: {self._datasize}\n"
            f"        sampletype: {self.sampletype} => {self.sampletype_str()}\n"
            f"    record pointer: {ct.c_void_p.from_buffer(self._record).value})"
        )

    def __lt__(self, obj):
        return (self.sourceid, self.starttime) < (obj.sourceid, obj.starttime)

    def __gt__(self, obj):
        return (self.sourceid, self.starttime) > (obj.sourceid, obj.starttime)

    def __le__(self, obj):
        return (self.sourceid, self.starttime) <= (obj.sourceid, obj.starttime)

    def __ge__(self, obj):
        return (self.sourceid, self.starttime) >= (obj.sourceid, obj.starttime)

    def __str__(self) -> str:
        return (
            f"{self.sourceid}, "
            f"{self.pubversion}, "
            f"{self.reclen}, "
            f"{self.samplecnt} samples, "
            f"{self.samprate} Hz, "
            f"{self.starttime_str()}"
        )

    @property
    def record(self) -> bytes:
        """Return raw, parsed miniSEED record as bytes"""
        if not self._record:
            raise ValueError("No raw record available")

        return self._record[: self._reclen]

    @property
    def reclen(self) -> int:
        """Return record length in bytes"""
        return self._reclen

    @reclen.setter
    def reclen(self, value) -> None:
        """Set maximum record length in bytes"""
        self._reclen = value

    @property
    def swapflag(self) -> int:
        """Return swap flags as raw integer

        Use MS3Record.swap_flag_dict() for a dictionary of decoded flags
        """
        return self._swapflag

    def swapflag_dict(self) -> dict:
        """Return swap flags as dictionary"""
        swapflag = {}
        if self._swapflag & MSSWAP_HEADER.value:
            swapflag["header_swapped"] = True
        else:
            swapflag["header_swapped"] = False
        if self._swapflag & MSSWAP_PAYLOAD.value:
            swapflag["payload_swapped"] = True
        else:
            swapflag["payload_swapped"] = False
        return swapflag

    @property
    def sourceid(self) -> str:
        """Return source identifier as string"""
        return self._sid.decode(encoding="utf-8")

    @sourceid.setter
    def sourceid(self, value) -> None:
        """Set source identifier

        The source identifier is limited to 64 characters.
        Typically this is an FDSN Source Identifier:
        https://docs.fdsn.org/projects/source-identifiers
        """
        self._sid = bytes(value, "utf-8")

    @property
    def formatversion(self) -> int:
        """Return format version"""
        return self._formatversion

    @formatversion.setter
    def formatversion(self, value) -> None:
        """Set format version"""
        if value not in [2, 3]:
            raise ValueError(f"Invalid miniSEED format version: {value}")

        self._formatversion = value

    @property
    def flags(self) -> int:
        """Return record flags as raw 8-bit integer

        Use MS3Record.flags_dict() for a dictionary of decoded flags
        """
        return self._flags

    @flags.setter
    def flags(self, value) -> None:
        """Set record flags as an 8-bit unsigned integer"""
        self._flags = value

    def flags_dict(self) -> dict:
        """Return record flags as a dictionary"""
        flags = {}
        if self._flags & ct.c_uint8(0x01).value:
            flags["calibration_signals_present"] = True
        if self._flags & ct.c_uint8(0x02).value:
            flags["time_tag_is_questionable"] = True
        if self._flags & ct.c_uint8(0x04).value:
            flags["clock_locked"] = True
        return flags

    @property
    def starttime(self) -> int:
        """Return start time as nanoseconds since Unix/POSIX epoch"""
        return self._starttime

    @starttime.setter
    def starttime(self, value) -> None:
        """Set start time as nanoseconds since Unix/POSIX epoch"""
        self._starttime = value

    @property
    def starttime_seconds(self) -> float:
        """Return start time as seconds since Unix/POSIX epoch"""
        return self._starttime / NSTMODULUS

    @starttime_seconds.setter
    def starttime_seconds(self, value) -> None:
        """Set start time as seconds since Unix/POSIX epoch

        The value is limited to microsecond resolution and will be rounded
        to to ensure a consistent conversion to the internal representation.
        """
        # Scale to microseconds, round to nearest integer, then scale to nanoseconds
        self._starttime = int(value * 1000000 + 0.5) * 1000

    def starttime_str(
        self, timeformat=TimeFormat.ISOMONTHDAY_Z, subsecond=SubSecond.NANO_MICRO_NONE
    ) -> str:
        """Return start time as formatted string"""
        c_timestr = ct.create_string_buffer(40)

        ms_nstime2timestr(self._starttime, c_timestr, timeformat, subsecond)

        return str(c_timestr.value, "utf-8")

    def set_starttime_str(self, value) -> None:
        """Set the start time using the specified provided date-time string"""
        self.starttime = ms_timestr2nstime(bytes(value, "utf-8"))

        if self.starttime == NSTERROR:
            raise ValueError(f"Invalid start time string: {value}")

    @property
    def samprate(self) -> float:
        """Return sample rate value as samples per second"""
        return _msr3_sampratehz(ct.byref(self))

    @samprate.setter
    def samprate(self, value) -> None:
        """Set sample rate

        When the value is positive it represents the rate in samples per second,
        when it is negative it represents the sample period in seconds.
        The specification recommends using the negative value sample period notation
        for rates less than 1 samples per second to retain resolution.

        Set to 0.0 if no time series data are included in the record, e.g. header-only
        record or text payload.
        """
        self._samprate = value

    @property
    def samprate_raw(self) -> float:
        """Return raw sample rate value

        This value represents samples per second when positive and sample interval
        in seconds when negative.  Use MSsRecord.samprate() for a consistent value in samples
        per second.
        """
        return self._samprate

    @property
    def encoding(self) -> int:
        """Return encoding format code.  Use MS3Record.encoding_str() for a readable description"""
        return self._encoding

    @encoding.setter
    def encoding(self, value) -> None:
        """Set encoding format code

        See https://docs.fdsn.org/projects/miniseed3/en/latest/data-encodings.html
        """
        self._encoding = value

    @property
    def pubversion(self) -> int:
        """Return publication version"""
        return self._pubversion

    @pubversion.setter
    def pubversion(self, value) -> None:
        """Set publication version"""
        self._pubversion = value

    @property
    def samplecnt(self) -> int:
        """Return sample count"""
        return self._samplecnt

    @property
    def crc(self) -> int:
        """Return CRC-32C from record header"""
        return self._crc

    @property
    def extralength(self) -> int:
        """Return length of extra headers"""
        return self._extralength

    @property
    def datalength(self) -> int:
        """Return length of encoded data payload in bytes"""
        return self._datalength

    @property
    def extra(self) -> str:
        """Return extra headers as string

        This is a JSON string, decodable to a dictionary with `json.loads(MS3Record.extra)`
        """
        return self._extra.decode(encoding="utf-8")

    @extra.setter
    def extra(self, value) -> None:
        """Set extra headers to specified JSON string"""
        status = _mseh_replace(
            ct.byref(self),
            value.encode(encoding="utf-8") if value is not None else None,
        )

        if status < 0:
            raise MseedLibError(status, f"Error replacing extra headers")

    @property
    def datasamples(self):
        """Return data samples as a ctype array of type `MS3Record.sampletype`

        The returned array can be used directly with slicing and indexing
        from `0` to `MS3Record.numsamples - 1`.

        The array can efficiently be copied to a _python list_ using:

            data_samples = MS3Record.datasamples[:]

        *NOTE* These data are owned by the this object instance and will be freed
        when the instance is destroyed.  If you wish to keep the data, you must
        make a copy.
        """
        if self.numsamples <= 0:
            raise ValueError("No decoded samples available")

        if self.sampletype == "i":
            return ct.cast(
                self._datasamples, ct.POINTER(ct.c_int32 * self.numsamples)
            ).contents
        elif self.sampletype == "f":
            return ct.cast(
                self._datasamples, ct.POINTER(ct.c_float * self.numsamples)
            ).contents
        elif self.sampletype == "d":
            return ct.cast(
                self._datasamples, ct.POINTER(ct.c_double * self.numsamples)
            ).contents
        elif self.sampletype == "t":
            return ct.cast(
                self._datasamples, ct.POINTER(ct.c_char * self.numsamples)
            ).contents
        else:
            raise ValueError(f"Unknown sample type: {self.sampletype}")

    @property
    def np_datasamples(self) -> Any:
        """Return data samples as a numpy array"""
        if self.numsamples <= 0:
            raise ValueError("No decoded samples available")

        try:
            import numpy as np  # lazy import
        except ImportError:
            raise ImportError(
                "numpy is not installed.  Install lib with [numpy] optional dependency"
            )

        # Translate libmseed sample type to numpy type
        nptype = {
            "i": np.int32,
            "f": np.float32,
            "d": np.float64,
            "t": np.char,
        }

        arr = np.frombuffer(self.datasamples, dtype=nptype[self.sampletype])
        return arr

    @property
    def datasize(self) -> int:
        """Return size of decoded data payload in bytes"""
        return self._datasize

    @property
    def numsamples(self) -> int:
        """Return number of decoded samples at MS3Record.datasamples"""
        return self._numsamples

    @property
    def sampletype(self) -> Optional[str]:
        """Return sample type code if available, otherwise None"""
        return (
            self._sampletype.decode(encoding="utf-8")
            if self._sampletype != b"\x00"
            else None
        )

    def sampletype_str(self) -> Optional[str]:
        """Return sample type as descriptive stringlet"""

        if self._sampletype == b"i":
            return "int32"
        elif self._sampletype == b"f":
            return "float32"
        elif self._sampletype == b"d":
            return "float64"
        elif self._sampletype == b"t":
            return "text"
        else:
            return None

    @property
    def endtime(self) -> int:
        """Return end time as nanoseconds since Unix/POSIX epoch"""
        return _msr3_endtime(ct.byref(self))

    @property
    def endtime_seconds(self) -> float:
        """Return end time as seconds since Unix/POSIX epoch"""
        return _msr3_endtime(ct.byref(self)) / NSTMODULUS

    def endtime_str(
        self, timeformat=TimeFormat.ISOMONTHDAY_Z, subsecond=SubSecond.NANO_MICRO_NONE
    ) -> str:
        """Return start time as formatted string"""
        c_timestr = ct.create_string_buffer(40)

        ms_nstime2timestr(self.endtime, c_timestr, timeformat, subsecond)

        return str(c_timestr.value, "utf-8")

    def encoding_str(self) -> str:
        """Return encoding format as descriptive string"""
        return ms_encodingstr(self._encoding).decode("utf-8")

    def print(self, details=0) -> None:
        """Print details of the record to stdout, with varying levels of `details`"""
        _msr3_print(ct.byref(self), details)

    def _record_handler_wrapper(self, record, record_length, handlerdata) -> None:
        """Callback function for msr3_pack()
        Ignore the handlerdata argument, which is passed at the Python level.

        Cast the record buffer to a ctypes array for use in Python and pass to handler.
        """
        self._record_handler(
            ct.cast(record, ct.POINTER((ct.c_char * record_length))).contents,
            self._record_handler_data,
        )

    def pack(
        self, handler, handlerdata=None, datasamples=None, sampletype=None, verbose=0
    ) -> tuple[int, int]:
        """Pack `datasamples` into miniSEED record(s) and call `handler()`

        The `handler(record, handlerdata)` function must accept two arguments:

                record:         A buffer containing a miniSEED record
                handlerdata:    The `handlerdata` value

        The handler function must use or copy the record buffer as the memory may be
        reused on subsequent iterations.

        If `datasamples` is not None, it must be a sequence of samples that can be
        packed into the type specified by `sampletype` and appropriate for MS3Record.encoding.
        If `datasamples` is None, any samples associated with the MS3Record will be packed.

        For more flexible packing of records, including multiple channels and rolling
        buffer support, `see MSTraceList.pack()`.

        Returns a tuple of (packed_samples, packed_records)
        """

        # Set hander function as ctypes callback function
        if not hasattr(self, "_record_handler") or (self._record_handler != handler):
            self._record_handler = handler

            RECORD_HANDLER = ct.CFUNCTYPE(
                None, ct.POINTER(ct.c_char), ct.c_int, ct.c_void_p
            )
            self._ctypes_record_handler = RECORD_HANDLER(self._record_handler_wrapper)

        self._record_handler_data = handlerdata

        pack_flags = ct.c_uint32(0)
        packed_samples = ct.c_int64(0)

        # Always flush data when packing
        pack_flags.value |= MSF_FLUSHDATA.value

        if datasamples is not None:
            msr_datasamples = self._datasamples
            msr_sampletype = self._sampletype
            msr_numsamples = self._numsamples
            msr_samplecnt = self._samplecnt

            len_datasamples = len(datasamples)

            if sampletype == "i":
                ctypes_data = (ct.c_int32 * len_datasamples)(*datasamples)
            elif sampletype == "f":
                ctypes_data = (ct.c_float * len_datasamples)(*datasamples)
            elif sampletype == "d":
                ctypes_data = (ct.c_double * len_datasamples)(*datasamples)
            elif sampletype == "t":
                ctypes_data = (ct.c_char * len_datasamples)(*datasamples)
            else:
                raise ValueError(f"Unknown sample type: {sampletype}")

            self._datasamples = ct.cast(ct.byref(ctypes_data), ct.c_void_p)
            self._sampletype = bytes(sampletype, "utf-8")
            self._numsamples = len_datasamples
            self._samplecnt = len_datasamples

        # Retain miniSEED "sequence number" if parsed record is v2
        if self.formatversion == 2 and self._record:
            # Extract sequence number from record, first 6 bytes are ASCII digits
            sequence_string = self._record[0:6].decode("utf-8")
            sequence_number = int(sequence_string)

            if self.extralength > 0:
                extra_headers = json.loads(self.extra)
                extra_headers.setdefault("FDSN", {})["Sequence"] = sequence_number
                self.extra = json.dumps(extra_headers, separators=(",", ":"))
            else:
                extra_headers = {"FDSN": {"Sequence": sequence_number}}
                self.extra = json.dumps(extra_headers, separators=(",", ":"))

        packed_records = _msr3_pack(
            ct.byref(self),
            self._ctypes_record_handler,
            None,
            ct.byref(packed_samples),
            pack_flags,
            verbose,
        )

        # Restore the original datasamples, stampletype, numsamples, samplecnt
        if datasamples is not None:
            self._datasamples = msr_datasamples
            self._sampletype = msr_sampletype
            self._numsamples = msr_numsamples
            self._samplecnt = msr_samplecnt

        if packed_records < 0:
            raise MseedLibError(packed_records, f"Error packing miniSEED record(s)")

        return (packed_samples.value, packed_records)


# Module-level C-function wrappers
_msr3_sampratehz = wrap_function(
    clibmseed, "msr3_sampratehz", ct.c_double, [ct.POINTER(MS3Record)]
)

_msr3_print = wrap_function(
    clibmseed, "msr3_print", None, [ct.POINTER(MS3Record), ct.c_int8]
)

_msr3_endtime = wrap_function(
    clibmseed, "msr3_endtime", ct.c_int64, [ct.POINTER(MS3Record)]
)

_mseh_replace = wrap_function(
    clibmseed, "mseh_replace", ct.c_int, [ct.POINTER(MS3Record), ct.c_char_p]
)

_msr3_pack = wrap_function(
    clibmseed,
    "msr3_pack",
    ct.c_int,
    [
        ct.POINTER(MS3Record),
        ct.c_void_p,
        ct.c_void_p,
        ct.POINTER(ct.c_int64),
        ct.c_uint32,
        ct.c_int8,
    ],
)
