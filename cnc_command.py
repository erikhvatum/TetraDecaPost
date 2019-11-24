from enum import Enum

class CncCommandCode(Enum):
    BLANK_LINE = auto()
    ASSIGNMENT = auto()
    SET_FEED = auto()
    RAPID = auto()
    FEED = auto()
    HOMEY = auto()
    HDSPIN = auto()
    EXT_COOLANT = auto()
    INT_COOLANT = auto()
    CYCLE800 = auto()
    CYCLE832 = auto()
    TRAORI = auto()
    TRAFOOF = auto()
    MSG = auto()
    SET_TOOL = auto()
    SWITCH_TOOL = auto()
    OTHER = auto()

class CncCommand:
    def __init__(self, cmd_code, cmd_str, params, comment):
        self.cmd_code = cmd_code
        self.cmd_str = cmd_str
        self.params = params
        self.comment = comment


