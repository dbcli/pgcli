#!/usr/bin/env python
"""
Example of how to call the prompt-toolkit version of the Python debugger (pdb).
"""
from prompt_toolkit.contrib.pdb import set_trace


def fibo(n):
    """
    Calculate fibonaci number.
    """
    if n == 10:
        set_trace()

    if n == 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibo(n-1) + fibo(n-2)


if __name__ == '__main__':
    fibo(20)
