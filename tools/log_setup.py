import os
import sys
import logging


LOG_PATH    = os.path.abspath(os.path.join(os.path.dirname(__file__), '../log'))
not os.path.isdir(LOG_PATH) and os.mkdir(LOG_PATH)
APPNAME     = os.path.splitext(os.path.split(sys.argv[0])[-1:][0])[0]
APPFILE     = os.path.join(LOG_PATH, APPNAME + ".log")
ADD_LEVELS  = ['VISUAL', 'VISUAL2', 'DEBUG3']

DEBUG       = int(os.environ.get('DEBUG', 1))
CCOLOR      = int(os.environ.get('CCOLOR', 1))
TOCONSOLE   = int(os.environ.get('TOCONSOLE', 1))


#######################################################

def ADD_VISLEV():
    logging.addLevelName(12, 'VISUAL')

    def _visual(self, msg, *AA, **KWA):
        if self.isEnabledFor(12):
            self._log(12, msg, AA, **KWA)

    logging.Logger.visual = _visual

ADD_VISLEV()

def GET_LOGGER(**kwa):

    appfile     = kwa.get('appfile', APPFILE)
    appname     = kwa.get('appname', APPNAME)
    #add_levels  = kwa.get('add_levels', [])

    _print(f"appname={appname}")
    _print(f"appfile={appfile}")
    not os.path.isfile(appfile) and _print("(new file)")

    logger = logging.getLogger(appname)  
    logger.setLevel(logging.DEBUG)  
    #logger.setLevel(0)

    formatter = logging.Formatter(  
        fmt='%(asctime)s | %(name)-12s | %(levelname)-7s | %(message)s',
        datefmt='%H:%M:%S',
        )

    t_formatter = logging.Formatter(  
        fmt='%(name)-12s | %(message)s',
        datefmt='%H:%M:%S',
        )

    c_formatter = logging.Formatter(  
        fmt='%(asctime)s | %(name)-12s | \033[32m%(levelname)-7s\033[0m | %(message)s',
        datefmt='%H:%M:%S',
        )

    if TOCONSOLE:
        handler	= logging.StreamHandler()
        #handler.setLevel(logging.DEBUG)
        handler.setLevel(0)

        _formatter = c_formatter if CCOLOR else t_formatter
        handler.setFormatter(_formatter)
        handler.setFormatter(_formatter)
        logger.addHandler(handler)

    handler = logging.FileHandler(appfile)
    #handler.setLevel(logging.DEBUG)  
    handler.setLevel(0)  
    handler.setFormatter(formatter) 
    logger.addHandler(handler) 

    logger.info(f"app '{appname}' logging START")
    #logger.spec("doesnt work?")
    return logger


#######################################################

def add_level(clev, lname):
    def _level_maker(clev):
        def __func(self, msg, *args, **kwa):
            if self.isEnabledFor(clev):
                self._log(clev, msg, args, **kwa)
        return __func

    logging.addLevelName(clev, lname.upper())

    func = _level_maker(clev)
    if not hasattr(logging.Logger, lname):
        setattr(logging.Logger, lname, func)
        _print("adding {} | {}".format(clev, lname))

## not working like it did with osc-clock.  oh well?  how many do we need to add.
#[add_level(11 + ix, lev) for ix, lev in enumerate(ADD_LEVELS)]

def _print(txt):
    if DEBUG:
        _file = os.path.splitext(os.path.split(__file__)[-1])[0]
        print(f"\033[33m{_file} | {txt}\033[0m", file=sys.stderr)

#######################################################


if __name__ == '__main__':
    _levels = ['VISUAL']
    lll = GET_LOGGER(add_levels=_levels, appname='SLICER')
    yyy = GET_LOGGER(add_levels=_levels, appname='SLICER4')
    yyy = GET_LOGGER()

    #print(lll)
    lll.warning("yo")
    print(dir(lll))
    yyy.visual("HI")
