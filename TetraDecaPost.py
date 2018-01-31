# (C) Erik Hvatum, Arcterik LLC 2018. All rights reserved.

"""PyTetraDecaPost (C) Erik Hvatum, Arcterik LLC 2018. All rights reserved.

Testing, verification, and rapid development Python implementation of TetraDecaPost. Primary/official
implementation, named simply "TetraDecaPost", is C++.
"""

import post_processor
import dmu65ul_post

if __name__ == '__main__':
    import argparse
    import sys
    parser = argparse.ArgumentParser('TetraDecaPost Python prototype implementation commandline interface.')
    parser.add_argument('command', type=str)
#   parser.add_argument(
#       '--forced-ultrasonic-state',
#       '-u',
#       type=bool,
#       default=None)
    parser.add_argument('--input', type=str, default='-')
    parser.add_argument('--output', type=str, default='-')
    args = parser.parse_args()
    input = sys.stdin if args.input=='-' else open(args.input, newline='\r\n')
    output = sys.stdout if args.output=='-' else open(args.output, mode='a', newline='\r\n')
    pp = DMU65UL_Post()
    pp.execute(input, output)