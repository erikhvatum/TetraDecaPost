# Copyright (c) 2019 by Erik Hvatum

import attr
import re
from .cnc_param import CncParam

@attr.s
class CncCommand:
    words = attr.ib(default=attr.Factory(list))
    comment = attr.ib(default='')

    @classmethod
    def from_mpf_line(cls, line, cms):
        r = cls()
        ret = [r]
        # Strip line number
        m = re.search(r'^\s*N\d+\s*', line)
        if m is not None:
            line = line[m.span()[1]:]

        # Pull out trailing comment
        c_idx = line.find(';')
        if c_idx != -1:
            r.comment = line[c_idx:].rstrip()
            line = line[:c_idx]

        # Remove any leading or trailing whitespace
        line = line.strip()

        # We don't yet need to handle quote or paren sections correctly
        r.words = line.split()

        return ret

    @property
    def mpf_line(self):
        line = ' '.join(self.words)
        if self.comment != '':
            line += ' ' + self.comment
        return line

    @property
    def nc(self):
        return ' '.join(self.words)

    def copy(self):
        return CncCommand(self.words.copy(), self.comment)