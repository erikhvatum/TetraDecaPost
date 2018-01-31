# (C) Erik Hvatum, Arcterik LLC 2018. All rights reserved.

import tool_path

class PostProcessor:
    def __init__(self):
        self.current_line_num = -1
        self.tool_path = tool_path.ToolPath()

    def execute(self, inputf, outputf, enable_buffer_inputf=False):
        self.current_line_num = -1
        if enable_buffer_inputf:
            input = inputf.read()
            input_lines = [s.trim() for s in input.split('\n')]
            for input_line in input_lines:
                self.process_line(input_line)

    def process_line(self, line):
        self.current_line_num += 1
