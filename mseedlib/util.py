import ctypes as ct
from .clib import clibmseed, wrap_function


ms_nstime2timestr = wrap_function(clibmseed, 'ms_nstime2timestr', ct.c_int,
                                  [ct.c_int64, ct.c_char_p, ct.c_int, ct.c_int])

ms_timestr2nstime = wrap_function(clibmseed, 'ms_timestr2nstime', ct.c_int64,
                                  [ct.c_char_p])

ms_samplesize = wrap_function(clibmseed, 'ms_samplesize', ct.c_char, [ct.c_uint8])

ms_encodingstr = wrap_function(clibmseed, 'ms_encodingstr', ct.c_char_p, [ct.c_uint8])

ms_errorstr = wrap_function(clibmseed, 'ms_errorstr', ct.c_char_p, [ct.c_int])

ms_encoding_sizetype = wrap_function(clibmseed, 'ms_encoding_sizetype', ct.c_int,
                                     [ct.c_uint8, ct.POINTER(ct.c_uint8), ct.c_char_p])

#int ms_encoding_sizetype (uint8_t encoding, uint8_t *samplesize, char *sampletype);

ms_sid2nslc = wrap_function(clibmseed, 'ms_nstime2timestrz', ct.c_int,
                            [ct.c_char_p, ct.c_char_p, ct.c_char_p, ct.c_char_p, ct.c_char_p])

ms_nslc2sid = wrap_function(clibmseed, 'ms_nslc2sid', ct.c_int,
                            [ct.c_char_p, ct.c_int, ct.c_uint16,
                             ct.c_char_p, ct.c_char_p, ct.c_char_p, ct.c_char_p])

# TODO, create functions for ms_sid2nslc and ms_nslc2sid
# extern int ms_sid2nslc (const char *sid, char *net, char *sta, char *loc, char *chan);
# extern int ms_nslc2sid (char *sid, int sidlen, uint16_t flags,
#                         const char *net, const char *sta, const char *loc, const char *chan);