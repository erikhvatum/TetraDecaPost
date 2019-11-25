# Copyright (c) 2019 by Erik Hvatum

from .cnc_command import CncCommand
from .cnc_machine_state import CncMachineState
from .flinereader import flinereader

class CncProgram:
    def __init__(self):
        self.commands = []

    def import_mpf(self, mpf_fpath):
        cms = CncMachineState()
        for line in flinereader(mpf_fpath):
            self.commands.append(CncCommand.from_mpf_line(line, cms))

    def transform_for_dmu65ul(self):
        pass
#       for cmd, line in zip(self.commands, range(10000)):
#           print(line, cmd)

    def export_mpf(self, mpf_fpath):
        pass
