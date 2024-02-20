#!/bin/env python3
import os
import sys
import argparse
from tools import INFILE_CONVERT


DEFAULT_DEST_DIR = "/tmp/wav_in/"
CFORMAT = "FILE_{:04d}.wav"



def parse_argv(argv):
    print(f"parse_argv: START from {argv[0]}")
    parser = argparse.ArgumentParser(description="cmd line options for standalone wcSlot demo")
    #parser.add_argument('-o', '--outfile', dest='outfile', type=str, help='where to save outfile (has default per fxn)')
    parser.add_argument('-i', '--infile', dest='infile', type=str, help='infile, to segment')

    args = parser.parse_args(argv[1:])

    return args



def main_test():
    args = parse_argv(sys.argv)

    if not args.infile:
        print("requires '-i infile'")
        return

    if not os.path.isfile(args.infile):
        print(f"no file '{args.infile}'")
        return

    for f in range(99):
        full_path = os.path.join(DEFAULT_DEST_DIR, CFORMAT.format(f))
        print(full_path)
        if os.path.isfile(full_path):
            continue
        else:
            break


    INFILE_CONVERT(args.infile, full_path, debug=0)
    assert(os.path.isfile(full_path))

if __name__ == '__main__':
    main_test()
