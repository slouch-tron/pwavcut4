#!/bin/env

import os
#import sys
import time

from tools import InfileGetter


def main_test():
    iii = InfileGetter()
    print(iii)

    iii.as_cli()


if __name__ == '__main__':
    main_test()
