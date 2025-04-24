import ctypes as ct
from .clib import clibmseed, wrap_function
from .definitions import *

ms_nstime2timestr = wrap_function(
    clibmseed,
    "ms_nstime2timestr",
    ct.c_int,
    [ct.c_int64, ct.c_char_p, ct.c_int, ct.c_int],
)

ms_timestr2nstime = wrap_function(
    clibmseed, "ms_timestr2nstime", ct.c_int64, [ct.c_char_p]
)

ms_samplesize = wrap_function(clibmseed, "ms_samplesize", ct.c_char, [ct.c_uint8])

ms_encodingstr = wrap_function(clibmseed, "ms_encodingstr", ct.c_char_p, [ct.c_uint8])

ms_errorstr = wrap_function(clibmseed, "ms_errorstr", ct.c_char_p, [ct.c_int])

ms_encoding_sizetype = wrap_function(
    clibmseed,
    "ms_encoding_sizetype",
    ct.c_int,
    [ct.c_uint8, ct.POINTER(ct.c_uint8), ct.c_char_p],
)

ms_sid2nslc_n = wrap_function(
    clibmseed,
    "ms_sid2nslc_n",
    ct.c_int,
    [
        ct.c_char_p,
        ct.c_char_p,
        ct.c_size_t,
        ct.c_char_p,
        ct.c_size_t,
        ct.c_char_p,
        ct.c_size_t,
        ct.c_char_p,
        ct.c_size_t,
    ],
)

ms_nslc2sid = wrap_function(
    clibmseed,
    "ms_nslc2sid",
    ct.c_int,
    [
        ct.c_char_p,
        ct.c_int,
        ct.c_uint16,
        ct.c_char_p,
        ct.c_char_p,
        ct.c_char_p,
        ct.c_char_p,
    ],
)

ms_sampletime = wrap_function(
    clibmseed, "ms_sampletime", ct.c_int64, [ct.c_int64, ct.c_int64, ct.c_double]
)


def nstime2timestr(
    nstime: int,
    timeformat=TimeFormat.ISOMONTHDAY_Z,
    subsecond=SubSecond.NANO_MICRO_NONE,
):
    """Convert a nanosecond timestamp to a date-time string"""
    c_timestr = ct.create_string_buffer(40)

    status = ms_nstime2timestr(nstime, c_timestr, timeformat, subsecond)

    if status is not None:
        return str(c_timestr.value, "utf-8")
    else:
        raise ValueError(f"Error converting timestamp: {nstime}")


def timestr2nstime(timestr: str) -> int:
    """Convert a date-time string to a nanosecond timestamp"""
    status = ms_timestr2nstime(timestr.encode())

    if status != NSTERROR:
        return status
    else:
        raise ValueError(f"Error converting date-time string: {timestr}")


def sourceid2nslc(sourceid: str) -> tuple:
    """Convert an FDSN source ID to a tuple of (net, sta, loc, chan)"""
    max_size = 11
    net = ct.create_string_buffer(max_size)
    sta = ct.create_string_buffer(max_size)
    loc = ct.create_string_buffer(max_size)
    chan = ct.create_string_buffer(max_size)

    status = ms_sid2nslc_n(
        sourceid.encode(), net, max_size, sta, max_size, loc, max_size, chan, max_size
    )

    if status == 0:
        return (
            net.value.decode(),
            sta.value.decode(),
            loc.value.decode(),
            chan.value.decode(),
        )
    else:
        raise ValueError("Invalid source ID: %s" % sourceid)


def nslc2sourceid(net: str, sta: str, loc: str, chan: str) -> str:
    """Convert network, station, location, channel codes to an FDSN source ID"""
    # sourceid = ct.create_string_buffer(LM_SIDLEN + 1)
    sourceid = ct.create_string_buffer(21)

    status = ms_nslc2sid(
        sourceid,
        LM_SIDLEN + 1,
        0,
        net.encode(),
        sta.encode(),
        loc.encode(),
        chan.encode(),
    )

    if status != -1:
        return sourceid.value.decode()
    else:
        raise ValueError("Invalid NSLC codes: %s,%s,%s,%s" % (net, sta, loc, chan))


def sampletime(nstime: int, offset: int, samprate: float) -> int:
    """Calculate nanosecond timestamp of a sample offset from a start time"""
    return ms_sampletime(nstime, offset, samprate)
