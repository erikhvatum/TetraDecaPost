# (C) Erik Hvatum 2019

def flinereader(fpath):
    '''flinereader is a generator function that yields the content of the file specified by fpath,
    one line at a time, with trailing linefeed or linefeed & carriage return removed.

    Usage example:
    for line in flinereader("/foo/bar/baz.txt"):
        print(line)'''

    fpath = str(fpath)
    with open(fpath) as f:
        line = f.readline()
        while line != '':
            if line[-2:] == '\r\n':
                line = line[:-2]
            elif line[-1] == '\n':
                line = line[:-1]
            yield line
            line = f.readline()
