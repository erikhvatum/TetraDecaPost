from .cnc_param import CncParam

class CncOperation:
    def __init__(self, mcs_idx):
        self.mcs_idx = mcs_idx
        self.commands = []
