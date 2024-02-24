#!/bin/env

#import os
#import sys
import time

from tools import InfileGetter


def main_test():
    iii = InfileGetter()
    print(iii)

    iii.as_cli()

    while True:
        print(iii)
        time.sleep(0.4)
        if iii.state == iii.STATES.READY:
            print(iii)
            break


if __name__ == '__main__':
    main_test()
