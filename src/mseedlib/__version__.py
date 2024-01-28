import os

# Package version
__version__ = '0.0.2'


def libmseed_version():
    """Return the version of libmseed used by this module"""
    module_path = os.path.abspath(os.path.dirname(__file__))
    libh = os.path.join(module_path, "libmseed.h")

    with open(libh, 'r') as f:
        for line in f:
            if line.startswith("#define LIBMSEED_VERSION"):
                return line.split()[2].replace('"', '')
