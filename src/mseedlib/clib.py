
import os
import ctypes as ct
from platform import system

# Determine the platform and load the appropriate local library
module_path = os.path.abspath(os.path.dirname(__file__))
platform_system = system()

if platform_system.lower().startswith("darwin"):
    libpath = os.path.join(module_path, 'libmseed', 'libmseed.dylib')
elif platform_system.lower().startswith("windows"):
    libpath = os.path.join(module_path, 'libmseed', 'libmseed.dll')
else:
    libpath = os.path.join(module_path, 'libmseed', 'libmseed.so')

clibmseed = ct.cdll.LoadLibrary(libpath)


def wrap_function(lib, funcname, restype, argtypes):
    """Simplify wrapping ctypes functions"""
    func = lib.__getattr__(funcname)
    func.restype = restype
    func.argtypes = argtypes
    return func
