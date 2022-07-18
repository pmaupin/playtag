#!/usr/bin/env python3
import os

data = open('xilbsd.txt', 'rt').read().split()
data = ((x.rsplit('/', 1)[-1], x) for x in data)

for num, (name, source) in enumerate(sorted(data)):
    os.symlink(source, 'downloads/%04d_%s' % (num, name))
