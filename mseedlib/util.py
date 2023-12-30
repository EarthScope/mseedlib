import ctypes as ct
from .clib import clibmseed, wrap_function
from .definitions import *

ms_nstime2timestr = wrap_function(clibmseed, 'ms_nstime2timestr', ct.c_int,
                                  [ct.c_int64, ct.c_char_p, ct.c_int, ct.c_int])

ms_timestr2nstime = wrap_function(clibmseed, 'ms_timestr2nstime', ct.c_int64,
                                  [ct.c_char_p])

ms_samplesize = wrap_function(clibmseed, 'ms_samplesize', ct.c_char, [ct.c_uint8])

ms_encodingstr = wrap_function(clibmseed, 'ms_encodingstr', ct.c_char_p, [ct.c_uint8])

ms_errorstr = wrap_function(clibmseed, 'ms_errorstr', ct.c_char_p, [ct.c_int])

ms_encoding_sizetype = wrap_function(clibmseed, 'ms_encoding_sizetype', ct.c_int,
                                     [ct.c_uint8, ct.POINTER(ct.c_uint8), ct.c_char_p])

ms_sid2nslc = wrap_function(clibmseed, 'ms_sid2nslc', ct.c_int,
                            [ct.c_char_p, ct.c_char_p, ct.c_char_p, ct.c_char_p, ct.c_char_p])

ms_nslc2sid = wrap_function(clibmseed, 'ms_nslc2sid', ct.c_int,
                            [ct.c_char_p, ct.c_int, ct.c_uint16,
                             ct.c_char_p, ct.c_char_p, ct.c_char_p, ct.c_char_p])


def sourceid2nslc(sourceid):
    """Convert an FDSN source ID to a tuple of (net, sta, loc, chan)"""
    net = ct.create_string_buffer(11)
    sta = ct.create_string_buffer(11)
    loc = ct.create_string_buffer(11)
    chan = ct.create_string_buffer(11)

    status = ms_sid2nslc(sourceid.encode(), net, sta, loc, chan)

    if status == 0:
        return (net.value.decode(), sta.value.decode(), loc.value.decode(), chan.value.decode())
    else:
        raise ValueError("Invalid source ID: %s" % sourceid)


def nslc2sourceid(net, sta=None, loc=None, chan=None):
    """Convert network, station, location, channel codes to an FDSN source ID"""
    sourceid = ct.create_string_buffer(LM_SIDLEN)

    status = ms_nslc2sid(sourceid, LM_SIDLEN, 0,
                         net.encode(),
                         sta.encode() if sta else None,
                         loc.encode() if loc else None,
                         chan.encode() if chan else None)

    if status != -1:
        return sourceid.value.decode()
    else:
        raise ValueError("Invalid NSLC: %s,%s,%s,%s" % (net, sta, loc, chan))
