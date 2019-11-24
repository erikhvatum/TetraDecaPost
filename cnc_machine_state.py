# (C) Erik Hvatum 2019

import attr

@attr.s
class CncMachineState:
    machine_name = attr.ib()
    feed_rate = attr.ib(init=False, default=None)
    workpiece_home_idx = attr.ib(init=False, default=None)
    cycle800 = attr.ib(init=False, default=None)
    cycle832 = attr.ib(init=False, default=None)
    traori = attr.ib(init=False, default=None)
    spindle_rotation_direction = attr.ib(init=False, default=None)
    spindle_idx = attr.ib(init=False, default=None)
    tool = attr.ib(init=False, default=None)
    next_tool = attr.ib(init=False, default=None)