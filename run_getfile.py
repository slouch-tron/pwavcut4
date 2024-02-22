#!/bin/env

import os
import sys
import time

from tools import InfileGetter




def main_test():
    iii = InfileGetter()
    args = iii.parse_argv(sys.argv)

    print(iii)
    iii.TestDL()
    while True:
        print(iii)
        time.sleep(0.8)


if __name__ == '__main__':
    main_test()
