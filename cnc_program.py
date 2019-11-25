# Copyright (c) 2019 by Erik Hvatum

import re
import sys
from .cnc_command import CncCommand
from .cnc_machine_state import CncMachineState
from .flinereader import flinereader

class CncProgram:
    def __init__(self):
        self.commands = []

    def import_mpf(self, mpf_fpath):
        cms = CncMachineState()
        for line in flinereader(mpf_fpath):
            self.commands.extend(CncCommand.from_mpf_line(line, cms))

    def export_mpf(self, mpf_fpath):
        with open(str(mpf_fpath), 'w') as out:
            for n, cmd in enumerate(self.commands):
                print(f'N{n}', cmd.mpf_line, file=out)

    def transform_for_dmu65ul(self):
        tool = None
        next_tool = None
        seen_camtol_def = False
        ncmds = []
        skip_lines = [
            'DEF REAL _X_HOME, _Y_HOME, _Z_HOME, _A_HOME, _C_HOME',
            '_X_HOME=0 _Y_HOME=0 _Z_HOME=0',
            '_A_HOME=0 _C_HOME=0',
            'SUPA G0 Z=_Z_HOME D0',
            'SUPA Z=_Z_HOME D0',
            'SUPA X=_X_HOME Y=_Y_HOME A=_A_HOME C=_C_HOME D1']
        replace_lines = {
            'CYCLE832(_camtolerance,0,1)' : 'CYCLE832(_camtolerance,_SEMIFIN,1)'}
        idx = -1
        yield 0.0
        try:
            while True:
                idx += 1
                if idx >= len(self.commands):
                    break
                if idx % 501 == 0:
                    yield idx / len(self.commands)
                in_cmd = self.commands[idx]
                in_nc = in_cmd.nc
                if in_nc in skip_lines:
                    continue
                if in_nc in replace_lines:
                    out_cmd = CncCommand()
                    out_cmd.words = [replace_lines[in_nc]]
                    ncmds.append(out_cmd)
                    continue
                if in_cmd.mpf_line == 'DEF REAL _camtolerance':
                    if not seen_camtol_def:
                        ncmds.append(in_cmd)
                        seen_camtol_def = True
                    continue
                ncmds.append(in_cmd)
        except:
            raise
        self.commands = ncmds
        yield 1.0
