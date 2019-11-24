# (C) Erik Hvatum 2019

from enum import Enum

class CncCommandCode(Enum):
    BLANK_LINE = auto()
    ASSIGNMENT = auto()
    RAPID = auto()
    FEED = auto()
    CW_ARC = auto()
    CCW_ARC = auto()
    HOMEY = auto()
    HDSPIN = auto()
    EXT_COOLANT = auto()
    INT_COOLANT = auto()
    CYCLE800 = auto()
    CYCLE832 = auto()
    SET_HOME_IDX = auto()
    TRAORI = auto()
    TRAFOOF = auto()
    MSG = auto()
    SET_TOOL = auto()
    SWITCH_TOOL = auto()
    OTHER = auto()

class CncCommand:
    def __init__(self, cmd_code=None, cmd_str=None, params=None, comment=None, sticky=False):
        self.cmd_code = cmd_code
        self.cmd_str = cmd_str
        self.params = params
        self.comment = comment
        self.sticky = 
