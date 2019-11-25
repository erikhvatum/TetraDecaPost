# Copyright (c) 2019 by Erik Hvatum

import attr

@attr.s
class CncParam:
    value = attr.ib()
    name = attr.ib(default='')
    delimiter = attr.ib(default='')
