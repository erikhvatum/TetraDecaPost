"""Testing and rapid development implementation of TetraDecaPost, in Python. Primary/official implementation is C++."""

import argparse
from pathlib import Path
import re

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        'TetraDecaPost testing and rapid development Python implementation commandline interface.',
        epilog='Either repost (r) or post (p) is required.')
    parser.add_argument('command', type=str)
    args = parser.parse_args()