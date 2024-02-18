#!/bin/env python3

import os
import sys
import re
import mido

DEBUG = int(os.environ.get('DEBUG', 0))


class portHolder():

    @property
    def port_i(self):
        if not hasattr(self, '_port_i'):
            self._port_i = None

        return self._port_i

    @property
    def port_o(self):
        if not hasattr(self, '_port_o'):
            self._port_o = None

        return self._port_o

    @property
    def port_c(self):
        if not hasattr(self, '_port_c'):
            self._port_c = None

        return self._port_c

    @property
    def port_f(self):
        if not hasattr(self, '_port_f'):
            self._port_f = None

        return self._port_f

    @port_i.setter
    def port_i(self, hint):
        self._port_i = GET_PORT(hint, iotype=0)

    @port_c.setter
    def port_c(self, hint):
        self._port_c = GET_PORT(hint, iotype=0)

    @port_o.setter
    def port_o(self, hint):
        self._port_o = GET_PORT(hint, iotype=1)

    @port_f.setter
    def port_f(self, hint):
        self._port_f = GET_PORT(hint, iotype=1)


    @staticmethod
    def GETPORT(*arg, **kwa):
        return GET_PORT(*arg, *kwa)


#### cant reach these like properties in the subclasses of this..
class portHolder2222():
    def __init__(self):
        self.port_i = None
        self.port_c = None
        self.port_o = None
        self.port_f = None

    def set_port_i(self, hint): self.port_i = GET_PORT(hint, iotype=0)
    def set_port_c(self, hint): self.port_i = GET_PORT(hint, iotype=0)
    def set_port_o(self, hint): self.port_i = GET_PORT(hint, iotype=1)
    def set_port_f(self, hint): self.port_i = GET_PORT(hint, iotype=1)




def dbprint(txt):
    if DEBUG:
        print(f"\033[33m{__file__}: {txt}\033[0m", file=sys.stderr)


def GET_PORT(hint, iotype=0):
    dbprint(" | ".join([
        "GET_PORT",
        f"hint={hint}",
        f"iotype={iotype}",
        ]))

    if hint == None:
        return

    _func = {
        0 : [mido.get_input_names, mido.open_input],
        1 : [mido.get_output_names, mido.open_output],
        2 : [mido.get_ioport_names, mido.open_ioport],
        }.get(iotype, None)

    if _func:
        for p in _func[0]():
            if re.search(hint.lower(), p.lower()):
                dbprint(p)
                return _func[1](p)

