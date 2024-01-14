import os

module_path = os.path.abspath(os.path.dirname(__file__))

# Module version
__version__ = None

with open(os.path.join(module_path, 'VERSION')) as version_file:
    __version__ = version_file.read().strip()


def libmseed_version():
    """Return the version of libmseed used by this module"""
    libh = os.path.join(module_path, 'libmseed', "libmseed.h")

    with open(libh, 'r') as f:
        for line in f:
            if line.startswith("#define LIBMSEED_VERSION"):
                return line.split()[2].replace('"', '')

