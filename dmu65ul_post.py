# (C) Erik Hvatum, Arcterik LLC 2018-2019. All rights reserved.

"""PyTetraDecaPost (C) Erik Hvatum, Arcterik LLC 2018-2019. All rights reserved.

Testing, verification, and rapid development Python implementation of TetraDecaPost. Primary/official
implementation, named simply "TetraDecaPost", is C++.
"""

import re

class DMU65UL_Post:
    def __init__(self):
        super().__init__()

    def run(self, inputf, outputf):
        line_num = -1
        line = inputf.readline()
        prev_was_rapid = False

        while line != '':
            line = line.strip()
            # print(' <= ', line)
            line_num += 1
#           if line.startswith('TOOL PATH/'):
#               match = re.match('''TOOL PATH/(.*),TOOL,(.*)''', line)
#               assert match is not None
#               print('T"{}"\nM6\nTRAORI\n'.format(match.group(2)), file=outputf)
#           elif line == 'RAPID':
            if line == 'RAPID':
                prev_was_rapid = True
            elif line.startswith('FEDRAT/IPM,'):
                print('G1 F{}'.format(line.split(',')[1]), file=outputf)
            elif line.startswith('FEDRAT/'):
                print('G1 F{}'.format(line.split('/')[1]), file=outputf)
            elif line.startswith('GOTO/'):
                values = line[len('GOTO/'):].split(',')
                value_count = len(values)
                if value_count == 3:
                    coords = 'X{} Y{} Z{}'.format(*values)
                elif value_count == 6:
                    coords = 'X{} Y{} Z{} A3={} B3={} C3={}'.format(*values)
                else:
                    raise RuntimeError('Bad value count - must be either 3 or 6, not {}.'.format(value_count))
                print('G0' if prev_was_rapid else 'G1', coords, file=outputf)
                prev_was_rapid = False
            line = inputf.readline()

if __name__ == '__main__':
    import argparse
    import sys
    parser = argparse.ArgumentParser('TetraDecaPost Python prototype implementation commandline interface.')
    parser.add_argument('--input', type=str, default='-')
    parser.add_argument('--output', type=str, default='-')
    args = parser.parse_args()
    input = sys.stdin if args.input == '-' else open(args.input, newline='\r\n')
    output = sys.stdout if args.output == '-' else open(args.output, mode='w', newline='\r\n')
    pp = DMU65UL_Post()
    pp.run(input, output)