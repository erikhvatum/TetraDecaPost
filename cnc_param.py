# (C) Erik Hvatum 2019

import attr

@attr.s
class CncParam:
    value = attr.ib()
    name = attr.ib(default='')
    delimiter = attr.ib(default='')
