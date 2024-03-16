import os
import sys
import logging
##from .defaults import LOG_PATH, DEBUG   ## this makes relative imports error


LOG_PATH    = os.path.abspath(os.path.join(os.path.dirname(__file__), '../log'))
APPNAME     = os.path.splitext(os.path.split(sys.argv[0])[-1:][0])[0]
APPFILE     = os.path.join(LOG_PATH, APPNAME + ".log")

DEBUG       = int(os.environ.get('DEBUG', 1))
CCOLOR      = int(os.environ.get('CCOLOR', 1))
TOCONSOLE   = int(os.environ.get('TOCONSOLE', 1))

DBCOL       = "36;2"

#######################################################

def GET_LOGGER(**kwa):

    appfile     = kwa.get('appfile', APPFILE)
    appname     = kwa.get('appname', APPNAME)

    _print(f"appname={appname:<20s} | appfile={appfile}")
    not os.path.isfile(appfile) and _print("new file '{appfile}'")

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
    return logger

#######################################################
def MK_LOGDIR():
    if not os.path.isdir(LOG_PATH):
        _print(f"make dir {LOG_PATH}")
        os.mkdir(LOG_PATH)

def ADD_VISLEV():
    _print("adding log level VISUAL")
    logging.addLevelName(12, 'VISUAL')

    def _visual(self, msg, *AA, **KWA):
        if self.isEnabledFor(12):
            self._log(12, msg, AA, **KWA)

    logging.Logger.visual = _visual

#######################################################
def _print(txt):
    if DEBUG:
        _file = os.path.splitext(os.path.split(__file__)[-1])[0]
        _col = "\033[%sm" %DBCOL
        print(f"{_col}{_file} | {txt}\033[0m", file=sys.stderr)

#######################################################

if __name__ != '__main__':
    ## here is good?
    ADD_VISLEV()
    MK_LOGDIR()

else:
    _levels = ['VISUAL']
    lll = GET_LOGGER(add_levels=_levels, appname='SLICER')
    yyy = GET_LOGGER(add_levels=_levels, appname='SLICER4')
    yyy = GET_LOGGER()

    #print(lll)
    lll.warning("yo")
    print(dir(lll))
    yyy.visual("HI")
