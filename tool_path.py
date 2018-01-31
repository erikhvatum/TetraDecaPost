# (C) Erik Hvatum, Arcterik LLC 2018. All rights reserved.

class Tool:
    def __init__(self, name=''):
        self.name = name

class ToolPath:
    def __init__(self):
        self.operations = []
        self.tool = Tool()
        self.name = ''