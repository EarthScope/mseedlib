
import os
import ctypes as ct

# Find the path to the shared library and load it
module_path = os.path.abspath(os.path.dirname(__file__))

if os.path.exists(os.path.join(module_path, 'libmseed.so')):
    libpath = os.path.join(module_path, 'libmseed.so')
elif os.path.exists(os.path.join(module_path, 'libmseed.dylib')):
    libpath = os.path.join(module_path, 'libmseed.dylib')
elif os.path.exists(os.path.join(module_path, 'libmseed.dll')):
    libpath = os.path.join(module_path, 'libmseed.dll')
else:
    raise Exception("Unable to find libmseed shared library")

clibmseed = ct.cdll.LoadLibrary(libpath)


def wrap_function(lib, funcname, restype, argtypes):
    """Simplify wrapping ctypes functions"""
    func = lib.__getattr__(funcname)
    func.restype = restype
    func.argtypes = argtypes
    return func
