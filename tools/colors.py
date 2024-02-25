#!/bin/env python

''' functions to fit lists of values for ansi color gradients,
        to stretch or shrink them to certain number of steps.
'''

def get_grad0(rate=100, debug=1):
    _clist = list(range(100, 200)) + [200] + list(range(200, 99, -1))
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

if __name__ == '__main__':
    ggg = get_grad0(rate=32, debug=0)
    hhh = get_grad1()

    print(ggg)
    print(f"  len=({len(ggg)})")
    #print(hhh)



