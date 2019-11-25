# Copyright (c) 2019 by Erik Hvatum

import attr

@attr.s
class CncMachineState:
    feed_rate = attr.ib(init=False, default=None)
    workpiece_home_id = attr.ib(init=False, default=None)
    cycle800 = attr.ib(init=False, default=None)
    cycle832 = attr.ib(init=False, default=None)
    traori = attr.ib(init=False, default=None)
    spindle_rotation_direction = attr.ib(init=False, default=None)
    spindle_idx = attr.ib(init=False, default=None)
    tool = attr.ib(init=False, default=None)
    next_tool = attr.ib(init=False, default=None)
    sticky = attr.ib(init=False, default=None)