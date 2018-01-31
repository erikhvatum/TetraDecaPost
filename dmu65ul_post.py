# (C) Erik Hvatum, Arcterik LLC 2018. All rights reserved.

import post_processor

class DMU65UL_Post(post_processor.PostProcessor):
    def __init__(self):
        super().__init__()

    def process_line(self, line):
        super().process_line(line)