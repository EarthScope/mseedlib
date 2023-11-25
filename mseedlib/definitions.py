import os
import ctypes as ct
from enum import IntEnum

# Constants and other defines from from libmseed.h
MAXRECLEN = 131172
LM_SIDLEN = 64
NSTMODULUS = 1000000000
NSTERROR = -2145916800000000000
NSTUNSET = -2145916799999999999

DE_TEXT = 0   # Text encoding (UTF-8)
DE_INT16 = 1   # 16-bit integer
DE_INT32 = 3   # 32-bit integer
DE_FLOAT32 = 4   # 32-bit float (IEEE)
DE_FLOAT64 = 5   # 64-bit float (IEEE)
DE_STEIM1 = 10  # Steim-1 compressed integers
DE_STEIM2 = 11  # Steim-2 compressed integers

MS_ENDOFFILE = 1  # End of file reached return value
MS_NOERROR = 0  # No error
MS_GENERROR = -1  # Generic unspecified error
MS_NOTSEED = -2  # Data not SEED
MS_WRONGLENGTH = -3  # Length of data read was not correct
MS_OUTOFRANGE = -4  # SEED record length out of range
MS_UNKNOWNFORMAT = -5  # Unknown data encoding format
MS_STBADCOMPFLAG = -6  # Steim, invalid compression flag(s)
MS_INVALIDCRC = -7  # Invalid CRC

MSF_UNPACKDATA = ct.c_uint32(0x0001)  # [Parsing] Unpack data samples
MSF_SKIPNOTDATA = ct.c_uint32(0x0002)  # [Parsing] Skip input that cannot be identified as miniSEED
MSF_VALIDATECRC = ct.c_uint32(0x0004)  # [Parsing] Validate CRC (if version 3)
MSF_PNAMERANGE = ct.c_uint32(0x0008)  # [Parsing] Parse and utilize byte range from path name suffix
MSF_ATENDOFFILE = ct.c_uint32(0x0010)  # [Parsing] Reading routine is at the end of the file
MSF_SEQUENCE = ct.c_uint32(0x0020)  # [Packing] UNSUPPORTED: Maintain a record-level sequence number
MSF_FLUSHDATA = ct.c_uint32(0x0040)  # [Packing] Pack all available data even if final record would not be filled
MSF_PACKVER2 = ct.c_uint32(0x0080)  # [Packing] Pack as miniSEED version 2 instead of 3
MSF_RECORDLIST = ct.c_uint32(0x0100)  # [TraceList] Build a ::MS3RecordList for each ::MS3TraceSeg
MSF_MAINTAINMSTL = ct.c_uint32(0x0200)  # [TraceList] Do not modify a trace list when packing

MSSWAP_HEADER = ct.c_uint8(0x01)  # Header needed byte swapping
MSSWAP_PAYLOAD = ct.c_uint8(0x02)  # Data payload needed byte swapping


class ctypesEnum(IntEnum):
    """A ctypes-compatible IntEnum superclass/"""
    @classmethod
    def from_param(cls, obj):
        return int(obj)


class TimeFormat(ctypesEnum):
    """Time format codes for ms_nstime2timestr() and ms_nstime2timestrz()"""
    ISOMONTHDAY = 0  # "YYYY-MM-DDThh:mm:ss.sssssssss", ISO 8601 in month-day format
    ISOMONTHDAY_Z = 1  # "YYYY-MM-DDThh:mm:ss.sssssssss", ISO 8601 in month-day format with trailing Z
    ISOMONTHDAY_DOY = 2  # "YYYY-MM-DD hh:mm:ss.sssssssss (doy)", ISOMONTHDAY with day-of-year
    ISOMONTHDAY_DOY_Z = 3  # "YYYY-MM-DD hh:mm:ss.sssssssss (doy)", ISOMONTHDAY with day-of-year and trailing Z
    ISOMONTHDAY_SPACE = 4  # "YYYY-MM-DD hh:mm:ss.sssssssss", same as ISOMONTHDAY with space separator
    ISOMONTHDAY_SPACE_Z = 5  # "YYYY-MM-DD hh:mm:ss.sssssssss", same as ISOMONTHDAY with space separator and trailing Z
    SEEDORDINAL = 6  # "YYYY,DDD,hh:mm:ss.sssssssss", SEED day-of-year format
    UNIXEPOCH = 7  # "ssssssssss.sssssssss", Unix epoch value
    NANOSECONDEPOCH = 8  # "sssssssssssssssssss", Nanosecond epoch value


class SubSecond(ctypesEnum):
    """Subsecond resolution codes for ms_nstime2timestr() and ms_nstime2timestrz()"""
    NONE = 0  # No subseconds
    MICRO = 1  # Microsecond resolution
    NANO = 2  # Nanosecond resolution
    MICRO_NONE = 3  # Microsecond resolution if subseconds are non-zero, otherwise no subseconds
    NANO_NONE = 4  # Nanosecond resolution if subseconds are non-zero, otherwise no subseconds
    NANO_MICRO = 5  # Nanosecond resolution if there are sub-microseconds, otherwise microseconds resolution
    NANO_MICRO_NONE = 6  # Nanosecond resolution if present, microsecond if present, otherwise no subseconds


class MS3Record(ct.Structure):
    """Structure to hold a miniSEED record"""
    _fields_ = [('record',        ct.POINTER(ct.c_char)),  # Raw miniSEED record, if available
                ('reclen',        ct.c_int32),   # Length of miniSEED record in bytes
                ('swapflag',      ct.c_uint8),   # Byte swap indicator (bitmask)
                ('sid',           ct.c_char * LM_SIDLEN),  # Source identifier
                ('formatversion', ct.c_uint8),   # Format major version
                ('flags',         ct.c_uint8),   # Record-level bit flags
                ('starttime',     ct.c_int64),   # Record start time (first sample)
                ('samprate',      ct.c_double),  # Nominal sample rate as samples/second (Hz) or period (s)
                ('encoding',      ct.c_int8),    # Data encoding format
                ('pubversion',    ct.c_uint8),   # Publication version
                ('samplecnt',     ct.c_int64),   # Number of samples in record
                ('crc',           ct.c_uint32),  # CRC of entire record
                ('extralength',   ct.c_uint16),  # Length of extra headers in bytes
                ('datalength',    ct.c_uint16),  # Length of data payload in bytes
                ('extra',         ct.c_char_p),  # Pointer to extra headers (JSON)
                ('datasamples',   ct.c_void_p),  # Data samples, 'numsamples' of type 'sampletype'
                ('datasize',      ct.c_size_t),  # Size of datasamples buffer in bytes
                ('numsamples',    ct.c_int64),   # Number of data samples in 'datasamples'
                ('sampletype',    ct.c_char)]    # Sample type code: t (text), i (int32) , f (float), d (double)
