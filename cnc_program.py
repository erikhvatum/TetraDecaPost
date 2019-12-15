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

    def apply_tool_preloading(self):
        idx = 0
        while idx < len(self.commands):
            if self.commands[idx].nc == 'M6':
                for ts_idx in range(idx+1, len(self.commands)):
                    nc = self.commands[ts_idx].nc
                    if nc.startswith('T=') or nc == 'T0':
                        break
                else:
                    break
                self.commands.insert(idx+1, self.commands.pop(ts_idx))
                idx = ts_idx
            else:
                idx += 1

    def pattern_ops_across_homes(self, count):
        HOMES = ['G54', 'G55', 'G56', 'G57', 'G58', 'G59']
        ncmds = []
        idx = 0
        while idx < len(self.commands):
            if self.commands[idx].nc == 'G54':
                for eidx in range(idx+1, len(self.commands)):
                    if self.commands[eidx].nc == 'CYCLE800()':
                        for hidx in range(count):
                            routine = [cmd.copy() for cmd in self.commands[idx:eidx]]
                            routine[0].words[0] = HOMES[hidx]
                            ncmds.extend(routine)
                        idx += len(routine)-1
                        break
                else:
                    raise RuntimeError('failed to find end of routine')
            else:
                ncmds.append(self.commands[idx])
            idx += 1
        self.commands = ncmds

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
            'SUPA X=_X_HOME Y=_Y_HOME A=_A_HOME C=_C_HOME D1',
            'SUPA X=_X_HOME Y=_Y_HOME A=_A_HOME C=_C_HOME',
            'SUPA Z=_Z_HOME'
        ]
        replace_lines = {
#           'CYCLE832(_camtolerance,0,1)' : 'CYCLE832(_camtolerance,_SEMIFIN,1)'
            }
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
                    ncmds.append(CncCommand(words=[replace_lines[in_nc]]))
                    continue
                match = re.match(r'(T="[^"]+"|T0|T=0) M6', in_nc)
                if match:
                    ncmds.append(CncCommand(words=[match.group(1)]))
                    ncmds.append(CncCommand(words=['M6']))
                    ncmds.append(CncCommand(words=['M11']))
                    continue
                if in_nc == 'DEF REAL _camtolerance':
                    if seen_camtol_def:
                        continue
                    seen_camtol_def = True
                    continue #!!!!!!!!!!
                elif in_nc.startswith('_camtolerance='):#!!!!!!!!!!
                    continue#!!!!!!!!!!
                elif in_nc.startswith('ORIRESET') and len(self.commands)-idx >= 6:
                    if self.commands[idx+1].nc == 'CYCLE832(_camtolerance,0,1)' and \
                      self.commands[idx+2].nc == 'COMPOF' and \
                      re.match(r'G5[456789]', self.commands[idx+3].nc) and \
                      self.commands[idx+4].nc == 'TRAORI' and \
                      'G0' in self.commands[idx+5].words:
                        match = re.match(r'ORIRESET\(([^,]+),([^,]+)\)', in_nc)
                        a, c = float(match.group(1)), float(match.group(2))
                        if a < 0:
                            a *= -1
                            c += 180
                        params = {v[0] : v for v in self.commands[idx+5].words if v != 'G0'}
                        ncmds.append(CncCommand(['HOMEY']))
                        ncmds.append(CncCommand(['M1']))
                        ncmds.append(CncCommand([self.commands[idx+3].nc]))
                        ncmds.append(CncCommand(['G0', f'A{a}', f'C{c}']))
                        ncmds.extend(CncCommand([v]) for v in ('G642', 'COMPCURV', 'FFWON', 'SOFT', 'CYCLE832(.002,_SEMIFIN,1)', 'TRAORI'))
                        ncmds.append(CncCommand(self.commands[idx+5].words + ['M8'], self.commands[idx+5].comment))
                        idx += 5
                        continue
                    else:
                        match = re.match(r'ORIRESET\(([^,]+),([^,]+)\)', in_nc)
                        a, c = float(match.group(1)), float(match.group(2))
                        if a < 0:
                            a *= -1
                            c += 180
                        ncmds.append(CncCommand(['HOMEY']))
                        ncmds.append(CncCommand(['M1']))
                        ncmds.append(CncCommand(['G0', f'A{a}', f'C{c}']))
                        continue
                elif in_nc == 'CYCLE832(_camtolerance,0,1)' and len(self.commands)-idx >= 3:
                    if self.commands[idx+1].nc == 'COMPOF' and re.match(r'G5[456789]', self.commands[idx+2].nc):
                        ncmds.extend(CncCommand([v]) for v in ('HOMEY', 'M1', self.commands[idx+2].nc, 'G642', 'COMPCURV',
                                                               'FFWON', 'SOFT', 'CYCLE832(.002,_SEMIFIN,1)'))
                        idx += 2
                        continue
                    else:
                        ncmds.extend(CncCommand([v]) for v in ('G642', 'COMPCURV', 'FFWON', 'SOFT', 'CYCLE832(.002,_SEMIFIN,1)'))
                        continue
                elif 'M3' in in_cmd.words or 'M4' in in_cmd.words:
                    ncmds.append(CncCommand(in_cmd.words + ['M8'], in_cmd.comment))
                    continue
                elif in_cmd.nc == 'M5':
                    ncmds.append(CncCommand(['M9']))
                    ncmds.append(CncCommand(['M5'], in_cmd.comment))
                    continue
                elif in_cmd.nc == 'COMPOF':
                    continue
                ncmds.append(CncCommand(list(in_cmd.words), in_cmd.comment))
        except Exception as e:
            print(e, sys.stderr)
            raise
        if ncmds:
            if ncmds[-1].nc == 'M30':
                ncmds.insert(-1, CncCommand(['HDSPIN']))
        self.commands = ncmds
        yield 1.0
