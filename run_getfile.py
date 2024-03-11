#!/bin/env

import os
#import sys
import time

from tools import InfileGetter
TOCONSOLE = int(os.environ.get('TOCONSOLE', 0))


def main_test():
    iii = InfileGetter()
    print(iii)

    iii.as_cli()

    try:
        while True:
            TOCONSOLE or print(iii)
            iii.Update()
            time.sleep(0.1)
            if iii.state in [iii.STATES.READY, iii.STATES.ERROR, iii.STATES.CANCEL]:
                print(iii)
                break
    except KeyboardInterrupt:
        iii.Cancel()


if __name__ == '__main__':
    main_test()
