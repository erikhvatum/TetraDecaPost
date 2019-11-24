# (C) Erik Hvatum 2019

from .cnc_operation import CncOperation
from .flinereader import flinereader

class CncProgram:
    def __init__(self):
        self.operations = []

    def import_mpf(self, mpf_fpath):
        for line in flinereader(mpf_fpath):


    def transform_for_dmu65ul(self):
        pass

    def export_mpf(self, mpf_fpath):
        pass
