#!/bin/env

#import os
#import sys
import time

from tools import InfileGetter


def main_test():
    iii = InfileGetter()
    print(iii)

    iii.as_cli()

    try:
        while True:
            print(iii)
            iii.Update()
            time.sleep(0.1)
            if iii.state == iii.STATES.READY:
                print(iii)
                break
    except KeyboardInterrupt:
        iii.Cancel()


if __name__ == '__main__':
    main_test()
