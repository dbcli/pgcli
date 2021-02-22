#!/usr/bin/env python
import sys


def wrappager(boundary):
    print(boundary)
    while 1:
        buf = sys.stdin.read(2048)
        if not buf:
            break
        sys.stdout.write(buf)
    print(boundary)


if __name__ == "__main__":
    wrappager(sys.argv[1])
