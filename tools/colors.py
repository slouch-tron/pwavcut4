#!/bin/env python
import os
import sys

import time

''' functions to fit lists of values for ansi color gradients,
        to stretch or shrink them to certain number of steps.
'''

## these are in infile_getter, should we define centrally here?
BLINKCOLORS = [56, 66, 76, 86]
BLINKCOLORS = [232, 238, 244, 250, 255, 231, 230, 229, 228, 227, 226, 225, 232, 232, 232, 232]
#BLINKCOLORS = [226, 232, 227, 232, 228, 232, 229, 232, 230, 232, 231, 232]
#BLINKCOLORS = list(range(16,21))


def get_grad0(clist=None, rate=100, debug=1):
    _clist = clist or list(range(100, 200)) + [200] + list(range(200, 99, -1))
    _olist = list()
    cc = 0
    
    _ll = len(_clist)
    if _ll < rate:
        for f in range(rate-1):
            cc += _ll / (rate-1)
            debug and print(f"{f} | {int(cc)},{cc} \t| ")
            _olist.append(_clist[int(cc)])

    elif _ll > rate:
        _olist.append(_clist[0])
        for f in range(0, rate-1):
            cc += _ll / (rate-1)
            debug and print(f"{f} | {int(cc)},{cc} \t| ")
            if _ll == int(cc):
                break

            _olist.append(_clist[int(cc)])

        _olist.append(_clist[-1])

    else:   ## ==
        _olist = [x for x in _clist]

    return _olist


def get_grad1(rate=1000):
    return list(range(100, 250))


'''
COLORS = dict(
    GRAD00=get_grad0(rate=22),
    GRAD01=get_grad1(),
    )
     '''
def terminal_test(blist=BLINKCOLORS, ftime=1/16):
    assert(blist)
    do_clear = int(os.environ.get('DOCLEAR', 0))
    print(f"\033[33mDOCLEAR={do_clear}\033[0m", file=sys.stderr)

    blist = get_grad0(rate=12, clist=blist)
    _start = time.time()

    try:
        frame_ct = 0
        delta = 0
        ix = 0
        btime = time.time() 

        while True:
            frame_ct += 1

            _time = time.time()

            delta += _time - _start
            if delta > (1/16):
                delta -= int(delta)
                ix += 1
                ix %= len(blist)
                if ix == 0:
                    btime = _time - _start

            ostr = " | ".join([
                f"{frame_ct:5d} {ix:3d}",
                f"{blist[ix]:3d}",
                f"\033[38;5;%sm" %blist[ix] + "#"*32 + "\033[0m",
                f"{delta:8.4f}",
                f"{btime:8.4f}",
                ])

            if do_clear:
                os.system("clear")
                print("frame, ix, list item, color string")

            print(ostr)

            time.sleep(ftime)

    except KeyboardInterrupt:
        print("\033[33mgot ctrl-c\033[0m")
        return
    




if __name__ == '__main__':
    terminal_test()
    exit()


    ggg = get_grad0(rate=(64*4), debug=0)
    hhh = get_grad1()

    print(ggg)
    print(f"  len=({len(ggg)})")
    #print(hhh)



