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
            library_message = library_error.decode('utf-8')
        else:
            library_message = f'Unknown error code: {self.status_code}'

        return f"{library_message} {':: ' + self.message if self.message else ''}"
