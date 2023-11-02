from .definitions import *
from .util import ms_errorstr


class MseedLibError(ValueError):
    """Exception for libmseed return values"""

    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message

    def __str__(self):
        return ms_errorstr(self.status_code).decode(encoding='utf-8')
