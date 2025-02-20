import ctypes as ct
import time
from typing import Any
from .clib import clibmseed, wrap_function
from .definitions import *
from .msrecord import MS3Record
from .util import ms_nstime2timestr, ms_encoding_sizetype
from .exceptions import *


class MS3RecordPtr(ct.Structure):
    """Structure to hold a pointer to a miniSEED record"""

    def __repr__(self) -> str:
        return (
            f"Pointer to {self.msr.sourceid}, "
            f'{self.filename.decode("utf-8")}, '
            f"byte offset: {self.fileoffset}"
        )

    @property
    def msr(self) -> MS3Record:
        """Return a constructed MS3Record"""
        if not hasattr(self, "_msrecord"):
            self._msrecord = self._msr.contents

        return self._msrecord


MS3RecordPtr._fields_ = [
    ("bufferptr", ct.c_char_p),
    ("fileptr", ct.c_void_p),
    ("filename", ct.c_char_p),
    ("fileoffset", ct.c_int64),
    ("_msr", ct.POINTER(MS3Record)),
    ("_endtime", ct.c_int64),
    ("_dataoffset", ct.c_uint32),
    ("_prvtptr", ct.c_void_p),
    ("_next", ct.POINTER(MS3RecordPtr)),
]


class MS3RecordList(ct.Structure):
    """Structure to hold a list of MS3RecordPtr entries"""

    def __repr__(self) -> str:
        return f"Record list of {self.recordcnt} records"

    def records(self) -> Any:
        """Return the records via a generator iterator"""
        current_record = self._first
        while current_record:
            yield current_record.contents
            current_record = current_record.contents._next


MS3RecordList._fields_ = [
    ("recordcnt", ct.c_uint64),
    ("_first", ct.POINTER(MS3RecordPtr)),
    ("_last", ct.POINTER(MS3RecordPtr)),
]


class TraceSegInfo(ct.Structure):
    """Structure to hold trace segment information"""

    def updated_str(
        self, timeformat=TimeFormat.ISOMONTHDAY_Z, subsecond=SubSecond.NANO_MICRO_NONE
    ) -> str:
        c_timestr = ct.create_string_buffer(40)

        ms_nstime2timestr(self.updated, c_timestr, timeformat, subsecond)

        return str(c_timestr.value, "utf-8")


TraceSegInfo._fields_ = [
    ("traceid_address", ct.c_void_p),  # Address of parent trace ID
    ("updated", ct.c_int64),
]  # Time of last segment update


class MS3TraceSeg(ct.Structure):
    """Structure to hold a trace segment"""

    def __repr__(self) -> str:
        return (
            f"start: {self.starttime_str()}, "
            f"end: {self.endtime_str()}, "
            f"samprate: {self.samprate}, "
            f"samples: {self.samplecnt} "
        )

    @property
    def info(self) -> TraceSegInfo:
        """Return the trace segment information structure"""

        if not self._prvtptr:
            # Allocate structure and store at _prvtptr
            raw_buffer = ct.create_string_buffer(ct.sizeof(TraceSegInfo))
            self._prvtptr = ct.cast(raw_buffer, ct.POINTER(TraceSegInfo))

        return self._prvtptr.contents

    @property
    def starttime_seconds(self) -> float:
        """Return start time as seconds since Unix/POSIX epoch"""
        return self.starttime / NSTMODULUS

    def starttime_str(
        self, timeformat=TimeFormat.ISOMONTHDAY_Z, subsecond=SubSecond.NANO_MICRO_NONE
    ) -> str:
        c_timestr = ct.create_string_buffer(40)

        ms_nstime2timestr(self.starttime, c_timestr, timeformat, subsecond)

        return str(c_timestr.value, "utf-8")

    @property
    def endtime_seconds(self) -> float:
        """Return end time as seconds since Unix/POSIX epoch"""
        return self.endtime / NSTMODULUS

    def endtime_str(
        self, timeformat=TimeFormat.ISOMONTHDAY_Z, subsecond=SubSecond.NANO_MICRO_NONE
    ) -> str:
        c_timestr = ct.create_string_buffer(40)

        ms_nstime2timestr(self.endtime, c_timestr, timeformat, subsecond)

        return str(c_timestr.value, "utf-8")

    @property
    def recordlist(self) -> MS3RecordList:
        """Return the record list structure"""
        if self._recordlist is None:
            raise ValueError("No record list available")

        return self._recordlist.contents

    @property
    def datasamples(self) -> Any:
        """Return data samples as a ctype array of type `MS3TraceSeg.sampletype`

        The returned array can be used directly with slicing and indexing
        from `0` to `MS3TraceSeg.numsamples - 1`.

        The array can efficiently be copied to a _python list_ using:

            data_samples = MS3TraceSeg.datasamples[:]

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
    def sampletype(self) -> str:
        """Return sample type code"""
        if self._sampletype != b"\x00":
            return self._sampletype.decode(encoding="utf-8")
        else:
            raise ValueError("No sample type available")

    @property
    def sample_size_type(self) -> tuple[int, str]:
        """Return data sample size and type code from first record in list"""
        sample_size = ct.c_uint8(0)
        sample_type = ct.c_char(0)

        if self.recordlist is None:
            raise ValueError(
                "No record list available to determine sample size and type"
            )

        # Determine sample size and type from the first record in the list
        status = ms_encoding_sizetype(
            self.recordlist._first.contents._msr.contents.encoding,
            ct.byref(sample_size),
            ct.byref(sample_type),
        )

        if status < 0:
            raise MseedLibError(MS_GENERROR, f"Error determining sample size and type")
        else:
            return (sample_size.value, sample_type.value.decode(encoding="utf-8"))

    def unpack_recordlist(self, buffer_pointer=None, buffer_bytes=0, verbose=0) -> int:
        """Unpack the data samples from the record list

        If `buffer_pointer` is provided, it must be a ctypes-style pointer to a buffer
        containing `buffer_bytes` of allocated memory to hold the data samples.

        *NOTE* If a `buffer_pointer` is not provided, these data will be owned
        by the this object instance and will be freed when the instance is
        destroyed. If you wish to keep the data, you must make a copy.
        """
        if self.recordlist is None:
            raise ValueError("No record list available to unpack")

        if self._datasamples is not None:
            raise ValueError("Data samples already unpacked")

        status = _mstl3_unpack_recordlist(
            ct.cast(self.info.traceid_address, ct.POINTER(MS3TraceID)),
            ct.byref(self),
            buffer_pointer,
            buffer_bytes,
            verbose,
        )

        if status < 0:
            raise MseedLibError(MS_GENERROR, f"Error unpacking data samples")
        else:
            return status

    @property
    def np_datasamples(self) -> Any:
        """Return data samples as a numpy array"""
        import numpy as np  # lazy import

        if self.recordlist is None:
            raise ValueError(
                "Record list required for numpy use record_list=True on MSTraceList creation"
            )

        nptype = {"i": np.int32, "f": np.float32, "d": np.float64, "t": np.char}

        (_, sample_type) = self.sample_size_type

        dtype = nptype[sample_type]

        # Allocate NumPy array for data samples
        data_samples = np.zeros(self.samplecnt, dtype=dtype)

        # Unpack data samples into allocated NumPy array
        self.unpack_recordlist(
            buffer_pointer=np.ctypeslib.as_ctypes(data_samples),
            buffer_bytes=data_samples.nbytes,
        )

        return data_samples


MS3TraceSeg._fields_ = [
    ("starttime", ct.c_int64),  # Time of first sample
    ("endtime", ct.c_int64),  # Time of last sample
    (
        "samprate",
        ct.c_double,
    ),  # Nominal sample rate as samples/second (Hz) or period (s)
    ("samplecnt", ct.c_int64),  # Number of samples in trace coverage
    ("_datasamples", ct.c_void_p),  # Data samples, 'numsamples' of type 'sampletype'
    ("datasize", ct.c_uint64),  # Size of datasamples buffer in bytes
    ("numsamples", ct.c_int64),  # Number of data samples in 'datasamples'
    (
        "_sampletype",
        ct.c_char,
    ),  # Sample type code: t (text), i (int32) , f (float), d (double)
    (
        "_prvtptr",
        ct.POINTER(TraceSegInfo),
    ),  # Private pointer, in this code: pointer TraceSegInfo
    (
        "_recordlist",
        ct.POINTER(MS3RecordList),
    ),  # Pointer to list of records for trace segment
    ("_prev", ct.POINTER(MS3TraceSeg)),  # Pointer to previous trace segment
    ("_next", ct.POINTER(MS3TraceSeg)),
]  # Pointer to next trace segment, NULL if last


class MS3TraceID(ct.Structure):
    """Structure to hold a trace ID"""

    def __repr__(self) -> str:
        return (
            f"{self.sourceid}, "
            f"version {self.pubversion}, "
            f"earliest {self.earliest_str()}, "
            f"latest {self.latest_str()}, "
            f"segments {self.numsegments} "
        )

    def segments(self) -> Any:
        """Return the trace segment structures via a generator iterator"""
        current_segment = self._first
        while current_segment:
            # Store the address to this parent trace ID
            current_segment.contents.info.traceid_address = ct.addressof(self)
            yield current_segment.contents
            current_segment = current_segment.contents._next

    @property
    def sourceid(self) -> str:
        return self.sid.decode("utf-8")

    @property
    def earliest_seconds(self) -> float:
        """Return earliest segment time as seconds since Unix/POSIX epoch"""
        return self.earliest / NSTMODULUS

    def earliest_str(
        self, timeformat=TimeFormat.ISOMONTHDAY_Z, subsecond=SubSecond.NANO_MICRO_NONE
    ) -> str:
        c_timestr = ct.create_string_buffer(40)

        ms_nstime2timestr(self.earliest, c_timestr, timeformat, subsecond)

        return str(c_timestr.value, "utf-8")

    @property
    def latest_seconds(self) -> float:
        """Return latest segment time as seconds since Unix/POSIX epoch"""
        return self.latest / NSTMODULUS

    def latest_str(
        self, timeformat=TimeFormat.ISOMONTHDAY_Z, subsecond=SubSecond.NANO_MICRO_NONE
    ) -> str:
        c_timestr = ct.create_string_buffer(40)

        ms_nstime2timestr(self.latest, c_timestr, timeformat, subsecond)

        return str(c_timestr.value, "utf-8")


MS3TraceID._fields_ = [
    ("sid", ct.c_char * LM_SIDLEN),  # Source identifier
    ("pubversion", ct.c_uint8),  # Publication version
    ("earliest", ct.c_int64),  # Time of earliest sample
    ("latest", ct.c_int64),  # Time of lastest sample
    ("_prvtptr", ct.c_void_p),  # Private pointer for general use, unused by library
    ("numsegments", ct.c_uint32),  # Number of trace segments
    ("_first", ct.POINTER(MS3TraceSeg)),  # Pointer to first of list of segments
    ("_last", ct.POINTER(MS3TraceSeg)),  # Pointer to last of list of segments
    ("_next", ct.POINTER(MS3TraceID) * MSTRACEID_SKIPLIST_HEIGHT),
    ("_height", ct.c_uint8),
]  # Height of skip list at 'next'


class MS3TraceList(ct.Structure):
    """Structure to hold a trace list"""

    _fields_ = [
        ("numtraceids", ct.c_uint32),  # Number of traces IDs in list
        (
            "_traces",
            MS3TraceID,
        ),  # Head node of trace skip list, first entry at \a traces.next[0]
        ("_prngstate", ct.c_uint64),
    ]  # INTERNAL: State for Pseudo RNG


class MSTraceList:
    """A container for a list of traces read from miniSEED

    If `input` is an integer, it is assumed to be an open file descriptor,
    otherwise it is assumed to be a path (file) name.  In all cases the
    file or descriptor will be closed when the objects close() is called.

    If `unpack_data` is True, the data samples will be decoded.

    If `skip_not_data` is True, bytes from the input stream will be skipped
    until a record is found.

    If `validate_crc` is True, the CRC will be validated if contained in
    the record (legacy miniSEED v2 contains no CRCs).  The CRC provides an
    internal integrity check of the record contents.

    The overall structure of the trace list list of trace IDs, each of which
    contains a list of trace segments illustrated as follows:
    - MSTraceList
      - TraceID
        - Trace Segment
        - Trace Segment
        - Trace Segment
        - ...
      - TraceID
        - Trace Segment
        - Trace Segment
        - ...
      - ...

    MSTraceList.traces() returns a generator iterator for the list of TraceIDs,
    and TraceID.segments() returns a generator iterator for the list of trace
    segments.

    Example usage iterating over the trace list:
    ```
    from mseedlib import MSTraceList

    mstl = MSTraceList('input_file.mseed')
    for traceid in mstl.traceids():
        print(f'{traceid.sourceid}, {traceid.pubversion}')
        for segment in traceid.segments():
            print(f'  {segment.starttime_str()} - {segment.endtime_str()}, ',
                  f'{segment.samprate} sps, {segment.samplecnt} samples')
    ```
    """

    def __init__(
        self,
        file_name=None,
        unpack_data=False,
        record_list=False,
        skip_not_data=False,
        validate_crc=True,
        split_version=False,
        verbose=0,
    ):
        self.parse_flags = ct.c_uint32(0)
        self.record_list = ct.c_int8(0)
        self.split_version = ct.c_int8(0)
        self._tolerance = ct.c_void_p()
        self._selections = ct.c_void_p()
        self._filenames = []
        self._record_handler = None

        # Allocate and initialize an MS3TraceList Structure
        self._mstl = _mstl3_init(None)

        # Read a specified input file into the trace list
        if file_name is not None:
            self.read_file(
                file_name,
                unpack_data=unpack_data,
                record_list=record_list,
                skip_not_data=skip_not_data,
                validate_crc=validate_crc,
                split_version=split_version,
                verbose=verbose,
            )

    def __repr__(self) -> str:
        repr = f"Trace List with {self.numtraceids} Source IDs\n"
        for traceid in self.traceids():
            repr += f"  {traceid}\n"
            for segment in traceid.segments():
                repr += f"    {segment}\n"

        return repr

    def __del__(self) -> None:
        """Free memory allocated at the C level for this MSTraceList"""

        # Disassociate the TraceSegInfo structures for segments
        for traceid in self.traceids():
            for segment in traceid.segments():
                if segment._prvtptr:
                    segment._prvtptr = None

        _mstl3_free(self._mstl, 0)

    @property
    def numtraceids(self) -> int:
        return self._mstl.contents.numtraceids

    def get_traceid(self, sourceid, version=0) -> MS3TraceID:
        """Return the requested trace ID structure"""
        traceid = _mstl3_findID(
            self._mstl, bytes(sourceid, "utf-8"), ct.c_uint8(version), None
        )

        if traceid:
            return traceid.contents
        else:
            raise NoSuchSourceID(sourceid)

    def traceids(self) -> Any:
        """Return the trace ID structures via a generator iterator"""
        current_traceid = self._mstl.contents._traces._next[0]
        while current_traceid:
            yield current_traceid.contents
            current_traceid = current_traceid.contents._next[0]

    def sourceids(self) -> Any:
        """Return the list of source IDs"""
        sources = []
        for traceid in self.traceids():
            sources.append(traceid.sourceid)
        return sources

    def print(
        self, details=0, gaps=False, versions=False, timeformat=TimeFormat.ISOMONTHDAY_Z
    ) -> None:
        """Print details of the trace list to stdout, with varying levels of `details`"""
        _details = ct.c_int8(details)
        _gaps = ct.c_int8(1 if gaps else 0)
        _versions = ct.c_int8(1 if versions else 0)

        _mstl3_printtracelist(self._mstl, timeformat, _details, _gaps, _versions)

    def read_file(
        self,
        file_name,
        unpack_data=False,
        record_list=False,
        skip_not_data=False,
        validate_crc=True,
        split_version=False,
        verbose=0,
    ) -> MS3TraceList:
        """Read a miniSEED file into the trace list"""
        # Store list of files names for reference and use in record lists
        self._filenames.append(bytes(file_name, "utf-8"))
        file_name_bytes = self._filenames[-1]

        self.parse_flags.value = 0

        if unpack_data:
            self.parse_flags.value |= MSF_UNPACKDATA.value

        if record_list:
            self.parse_flags.value |= MSF_RECORDLIST.value

        if skip_not_data:
            self.parse_flags.value |= MSF_SKIPNOTDATA.value

        if validate_crc:
            self.parse_flags.value |= MSF_VALIDATECRC.value

        status = _ms3_readtracelist_selection(
            ct.byref(self._mstl),
            file_name_bytes,
            self._tolerance,
            self._selections,
            self.split_version,
            self.parse_flags,
            verbose,
        )

        if status == MS_NOERROR:
            return self
        else:
            raise MseedLibError(status, f"Error reading miniSEED record")

    def add_data(
        self,
        sourceid: str,
        data_samples: list,
        sample_type: str,
        sample_rate: float,
        start_time_str: str = None,
        start_time: int = None,
        start_time_seconds: float = None,
        publication_version: int = 0,
    ):
        """Add data samples to the trace list for the specified source ID

        Data samples will be added to any existing trace segments that match.
        If no matching trace segment is found, a new trace segment will be created.

        The `sourceid` argument should be a valid FDSN source ID.

        The `data_samples` argument should be a list of values to add.

        The start time, or time of the first sample, can be specified in one
        of three ways, used in this order of preference:
            start_time:         nanoseconds since the epoch (full nanosecond resolution)
            start_time_seconds: seconds since the epoch (limited to microseconds)
            start_time_str:     date-time string
        """
        msr = MS3Record()

        if sample_type not in ["i", "f", "d", "t"]:
            raise ValueError(f"Invalid sample type: {sample_type}")

        msr.sourceid = sourceid
        msr.samprate = sample_rate
        msr.pubversion = publication_version

        if start_time is not None:
            msr.starttime = start_time
        elif start_time_seconds is not None:
            msr.starttime_seconds = start_time_seconds
        elif start_time_str is not None:
            msr.set_starttime_str(start_time_str)
        else:
            raise ValueError(
                "Must specify either start_time, start_time_seconds or start_time_str"
            )

        msr._sampletype = sample_type.encode(encoding="utf-8")
        msr._numsamples = len(data_samples)
        msr._samplecnt = msr._numsamples

        # Create an appropriate ctypes array of the data samples
        if sample_type == "i":
            msr._datasamples = ct.cast(
                (ct.c_int32 * msr._numsamples)(*data_samples), ct.c_void_p
            )
        elif sample_type == "f":
            msr._datasamples = ct.cast(
                (ct.c_float * msr._numsamples)(*data_samples), ct.c_void_p
            )
        elif sample_type == "d":
            msr._datasamples = ct.cast(
                (ct.c_double * msr._numsamples)(*data_samples), ct.c_void_p
            )
        elif sample_type == "t":
            msr._datasamples = ct.cast(
                (ct.c_char * msr._numsamples)(*data_samples), ct.c_void_p
            )

        # Add the MS3Record to the trace list, setting auto-heal flag to 1 (true)
        segptr = _mstl3_addmsr_recordptr(self._mstl, ct.byref(msr), None, 0, 1, 0, None)

        if segptr is None:
            raise MseedLibError(MS_GENERROR, f"Error adding data samples")

        # Set the updated time to the current time
        segptr.contents.info.updated = int(time.time() * NSTMODULUS + 0.5)

    def _record_handler_wrapper(self, record, record_length, handlerdata):
        """Callback function for mstl3_pack()
        Ignore the handlerdata argument, which is passed at the Python level.

        Cast the record buffer to a ctypes array for use in Python and pass to handler.
        """
        self._record_handler(
            ct.cast(record, ct.POINTER((ct.c_char * record_length))).contents,
            self._record_handler_data,
        )

    def pack(
        self,
        handler,
        handlerdata=None,
        flush_data=True,
        record_length=4096,
        encoding=DataEncoding.STEIM1,
        format_version=None,
        extra_headers=None,
        verbose=0,
    ) -> tuple[int, int]:
        """Pack data into miniSEED record(s) and call `handler()`

        The `handler(record, handlerdata)` function must accept two arguments:

                record:         A buffer containing a miniSEED record
                handlerdata:    The `handlerdata` value

        The handler function must use or copy the record buffer as the memory may be
        reused on subsequent iterations.

        If `flush_data` is True, all data samples will be packed.  In the case of
        miniSEED format version 2, this will likely create unfilled final records.

        If `flush_data` is False, as many fully-packed records will be created as
        possible.  Packed samples will be removed from the trace list.  This is useful
        for creating a rolling buffer of data for packing into miniSEED records.
        To flush any remaining, buffered data samples, a final call to pack() with
        `flush_data` set to True is required.

        The `record_length` argument specifies the maximum length of the packed
        records in bytes.

        The `encoding` argument specifies the data sample encoding to use for the
        packed records.  The value must be one of the DataEncoding enum values and
        approproate for the data sample type.

        The `format_version` argument specifies the miniSEED format version to
        create, either 2 or 3.

        The `extra_headers`, if specified, must be JSON-formatted extra headers
        that will be added to the record(s).

        Returns a tuple of (packed_samples, packed_records)
        """

        # Set handler function as ctypes callback function
        if not hasattr(self, "_record_handler") or (self._record_handler != handler):
            self._record_handler = handler

            RECORD_HANDLER = ct.CFUNCTYPE(
                None, ct.POINTER(ct.c_char), ct.c_int, ct.c_void_p
            )
            self._ctypes_record_handler = RECORD_HANDLER(self._record_handler_wrapper)

        self._record_handler_data = handlerdata

        pack_flags = ct.c_uint32(0)
        packed_samples = ct.c_int64(0)

        if flush_data:
            pack_flags.value |= MSF_FLUSHDATA.value

        if format_version is not None:
            if format_version not in [2, 3]:
                raise ValueError(f"Invalid miniSEED format version: {format_version}")

            if format_version == 2:
                pack_flags.value |= MSF_PACKVER2.value

        packed_records = _mstl3_pack(
            self._mstl,
            self._ctypes_record_handler,
            None,
            record_length,
            encoding,
            ct.byref(packed_samples),
            pack_flags,
            verbose,
            extra_headers.encode("utf-8") if extra_headers else None,
        )

        if packed_records < 0:
            raise MseedLibError(packed_records, f"Error packing miniSEED record(s)")

        return (packed_samples.value, packed_records)


# Module-level C-function wrappers
_mstl3_init = wrap_function(
    clibmseed, "mstl3_init", ct.POINTER(MS3TraceList), [ct.POINTER(MS3TraceList)]
)

_mstl3_free = wrap_function(
    clibmseed, "mstl3_free", None, [ct.POINTER(ct.POINTER(MS3TraceList)), ct.c_int8]
)

_mstl3_findID = wrap_function(
    clibmseed,
    "mstl3_findID",
    ct.POINTER(MS3TraceID),
    [ct.POINTER(MS3TraceList), ct.c_char_p, ct.c_uint8, ct.c_void_p],
)

_mstl3_printtracelist = wrap_function(
    clibmseed,
    "mstl3_printtracelist",
    None,
    [ct.POINTER(MS3TraceList), ct.c_int, ct.c_int8, ct.c_int8, ct.c_int8],
)

_ms3_readtracelist_selection = wrap_function(
    clibmseed,
    "ms3_readtracelist_selection",
    ct.c_int,
    [
        ct.POINTER(ct.POINTER(MS3TraceList)),
        ct.c_char_p,
        ct.c_void_p,
        ct.c_void_p,
        ct.c_int8,
        ct.c_uint32,
        ct.c_int8,
    ],
)

_mstl3_pack = wrap_function(
    clibmseed,
    "mstl3_pack",
    ct.c_int64,
    [
        ct.POINTER(MS3TraceList),
        ct.c_void_p,
        ct.c_void_p,
        ct.c_int,
        ct.c_int8,
        ct.POINTER(ct.c_int64),
        ct.c_uint32,
        ct.c_int8,
        ct.c_char_p,
    ],
)

_mstl3_unpack_recordlist = wrap_function(
    clibmseed,
    "mstl3_unpack_recordlist",
    ct.c_int64,
    [
        ct.POINTER(MS3TraceID),
        ct.POINTER(MS3TraceSeg),
        ct.c_void_p,
        ct.c_uint64,
        ct.c_int8,
    ],
)

_mstl3_addmsr_recordptr = wrap_function(
    clibmseed,
    "mstl3_addmsr_recordptr",
    ct.POINTER(MS3TraceSeg),
    [
        ct.POINTER(MS3TraceList),
        ct.POINTER(MS3Record),
        ct.c_void_p,
        ct.c_int8,
        ct.c_int8,
        ct.c_uint32,
        ct.c_void_p,
    ],
)
