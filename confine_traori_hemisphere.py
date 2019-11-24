#!/usr/bin/env python
# (C) Erik Hvatum, Arcterik LLC 2019. All rights reserved.

import math
import re

class ConfineTraoriHemisphere:
    '''This simple implementation attempts to traverse to the A>=0 hemisphere on a 5-axis AC table machine at the beginning
    of every set of consecutive G0 operations.'''
    def run(self, inputf, outputf):
        line_num = -1
        line = inputf.readline()
        in_Gx = None
        shortvalids = set(('X', 'Y', 'Z'))
        longvalids = set(('A3=', 'B3=', 'C3='))
        name_to_lit = {'X':'x','Y':'y','Z':'z','A3=':'i','B3=':'j','C3=':'k'}
        max_c3=-999999999999999
        xyz_ijk = dict(i=0,j=0,k=1)

        while line != '':
            line = line.strip()
            line_num += 1
            match = re.match('\s*N\d+\s*(.*)', line, flags=re.IGNORECASE)
            if match:
                line = match.group(1).strip()
            components = re.split('\s+', line)
            is_G = False
            if components[0] == 'G0':
                in_Gx = 0
                is_G = True
                components.pop(0)
            elif components[0] == 'G1':
                in_Gx = 1
                is_G = True
                components.pop(0)
            seen_component_names = set()
            ok = True
            hasValue = False
            for component in components:
                component = component.upper()
                if component[0:1] in shortvalids:
                    component_name, component_value = component[0], component[1:]
                    hasValue = True
                elif component[:3] in longvalids:
                    component_name, component_value = component[:3], component[3:]
                    hasValue = True
                elif component[0:1] == ';':
                    break
                else:
                    ok = False
                    break
                if component_name in seen_component_names:
                    raise RuntimeError('component {} is specified more than once in a block'.format(component_name))
                seen_component_names.add(component_name)
                xyz_ijk[name_to_lit[component_name]] = float(component_value)
            if ok and hasValue and is_G:
                x, y, z, i, j, k = (xyz_ijk[k] for k in 'xyzijk')
                # Note: we always want to use the solution for A and C in which A is either positive or very close to zero
                if k < .99:
                    l = math.sqrt(i*i+j*j)
                    i_n = i / l
                    j_n = j / l
#                   k_n = k / l
#               print(k_n)
                a = math.acos(k) * ( 360 / (2*math.pi) )
                c = 90 + math.asin(j_n) * ( 360 / (2*math.pi) )
                if a < 0:
                    print(a)
                print('N{:06} G{} X{} Y{} Z{} A={} C={}'.format(line_num, in_Gx, x, y, z, a, c), file=outputf)
            else:
                print('N{:06} {}'.format(line_num, line), file=outputf)
            line = inputf.readline()


if __name__ == '__main__':
    import argparse
    import sys
    parser = argparse.ArgumentParser('TRAORI-mode hemisphere containment for I,J,K tool vector format commandline interface.')
    parser.add_argument('--input', type=str, default='-')
    parser.add_argument('--output', type=str, default='-')
    args = parser.parse_args()
    input = sys.stdin if args.input == '-' else open(args.input, newline='\r\n')
    output = sys.stdout if args.output == '-' else open(args.output, mode='w', newline='\r\n')
    c = ConfineTraoriHemisphere()
    c.run(input, output)
