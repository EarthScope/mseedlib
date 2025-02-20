from .definitions import *
from .util import ms_errorstr


class MseedLibError(ValueError):
    """Exception for libmseed return values"""

    def __init__(self, status_code, message=None):
        self.status_code = status_code
        self.message = message

    def __str__(self):
        library_error = ms_errorstr(self.status_code)

        if library_error is not None:
            library_message = library_error.decode("utf-8")
        else:
            library_message = f"Unknown error code: {self.status_code}"

        return f"{library_message} {':: ' + self.message if self.message else ''}"


class NoSuchSourceID(ValueError):
    """Exception for non-existent trace source IDs"""

    def __init__(self, sourceid):
        self.sourceid = sourceid

    def __str__(self):
        return f"Source ID not found: {self.sourceid}"
