from enum import Enum

class CncCommandCode(Enum):
    BLANK_LINE = auto()
    ASSIGNMENT = auto()
    SET_FEED = auto()
    RAPID = auto()
    FEED = auto()
    HOMEY = auto()
    HDSPIN = auto()

class CncCommand:
    def __init__(self, cmd_code, cmd_str, params, comment):
        self.cmd_code = cmd_code
        self.cmd_str = cmd_str
        self.params = params
        self.comment = comment


