import ctypes as ct
from .clib import clibmseed, wrap_function


ms_nstime2timestr = wrap_function(clibmseed, 'ms_nstime2timestr', ct.c_int,
                                  [ct.c_int64, ct.c_char_p, ct.c_int, ct.c_int])

ms_timestr2nstime = wrap_function(clibmseed, 'ms_timestr2nstime', ct.c_int64,
                                  [ct.c_char_p])

ms_encodingstr = wrap_function(clibmseed, 'ms_encodingstr', ct.c_char_p, [ct.c_uint8])

ms_errorstr = wrap_function(clibmseed, 'ms_errorstr', ct.c_char_p, [ct.c_int])

#libmseed_malloc = wrap_function(clibmseed, 'libmseed_memory.malloc', ct.c_void_p, [ct.c_size_t])
#libmseed_realloc = wrap_function(clibmseed, 'libmseed_memory.realloc', ct.c_void_p, [ct.c_void_p, ct.c_size_t])
#libmseed_free = wrap_function(clibmseed, 'libmseed_memory.free', None, [ct.c_void_p])
